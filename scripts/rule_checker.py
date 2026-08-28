#!/usr/bin/env python3
"""
Rule Checker script for NetSage AI.
Deterministic rule checks for common network misconfigurations in show-command outputs.
Dependencies: standard library only (csv, re, sys, os).
"""

import csv
import re
import sys
import os

def check_duplicate_ip(show_output: str):
    """
    Regex-extract IPs following 'IP:' or in DHCP-binding-style lines.
    Flag if any IP appears more than once.
    """
    if not show_output:
        return None
    
    # Extract IPs after 'IP:' or 'IP Address:' or in binding lines (e.g., 10.0.10.5 ...)
    # Match IP addresses following IP: or IP Address: or standard IPv4 patterns in table rows
    ip_pattern = r'(?:IP:\s*|IP\s+Address:\s*|\b)([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b'
    
    # Specifically targeted IP extraction for host IP declarations and DHCP binding lines
    target_ips = []
    lines = show_output.split('|')
    for line in lines:
        # Match lines like "PC1> ipconfig|IP: 10.0.10.10" or DHCP binding rows "10.0.10.10 0100.5e7a..."
        m_ip = re.search(r'IP:\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', line, re.IGNORECASE)
        if m_ip:
            target_ips.append(m_ip.group(1))
        else:
            # Check DHCP binding style line: IP followed by MAC/Hardware address
            m_binding = re.search(r'\b([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+(?:[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}|[0-9a-f]{2}-[0-9a-f]{2})', line, re.IGNORECASE)
            if m_binding:
                target_ips.append(m_binding.group(1))

    # Also check general explicit IP occurrences if target_ips empty
    if not target_ips:
        all_found = re.findall(r'IP:\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', show_output, re.IGNORECASE)
        target_ips = all_found

    counts = {}
    duplicates = []
    for ip in target_ips:
        counts[ip] = counts.get(ip, 0) + 1
        if counts[ip] == 2:
            duplicates.append(ip)

    if duplicates:
        return f"Duplicate IP address detected: {', '.join(duplicates)}"
    return None

def check_wrong_mask(show_output: str):
    """
    Regex-extract all subnet masks (255.x.x.x pattern) in the blob.
    Flag if more than one distinct mask appears where the case implies a single segment.
    """
    if not show_output:
        return None
    
    masks = re.findall(r'\b(255\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\b', show_output)
    distinct_masks = set(masks)
    
    if len(distinct_masks) > 1:
        return f"Mismatched/multiple subnet masks detected in segment: {', '.join(sorted(distinct_masks))}"
    return None

def check_gateway_mismatch(show_output: str):
    """
    Extract 'IP:' and 'GW:' values, compare first 3 octets (/24 assumption),
    flag if they differ (host and gateway not in same subnet).
    """
    if not show_output:
        return None
    
    ip_match = re.search(r'IP:\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', show_output, re.IGNORECASE)
    gw_match = re.search(r'GW:\s*([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', show_output, re.IGNORECASE)
    
    if ip_match and gw_match:
        ip = ip_match.group(1)
        gw = gw_match.group(1)
        
        ip_octets = ip.split('.')[:3]
        gw_octets = gw.split('.')[:3]
        
        if ip_octets != gw_octets:
            return f"Gateway subnet mismatch: Host IP ({ip}) and Gateway ({gw}) are on different subnets"
    return None

def check_missing_route(show_output: str, expected_subnet_hint: str = None):
    """
    If 'show ip route' appears in the text but the expected subnet string doesn't appear anywhere after it,
    flag missing route.
    """
    if not show_output:
        return None
    
    if "show ip route" in show_output.lower():
        # Split on 'show ip route' to check output block
        parts = re.split(r'show ip route', show_output, flags=re.IGNORECASE)
        route_output = parts[-1]
        
        # If expected subnet hint provided, test explicitly
        if expected_subnet_hint:
            if expected_subnet_hint not in route_output:
                return f"Missing expected route for subnet '{expected_subnet_hint}' in routing table output"
        else:
            # General check: if routing table is empty or missing expected destination networks
            if "0.0.0.0/0" not in route_output and not re.search(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}', route_output):
                return "Routing table contains no active IPv4 subnet routes"
    return None

def check_interface_down(show_output: str):
    """
    Regex-check if any physical interface is in down/down or administratively down state.
    """
    if not show_output:
        return None
    
    # Check for administratively down or down/down in interface brief or show interface
    m_admin = re.search(r'\b((?:Serial|FastEthernet|GigabitEthernet|Eth|Fa|Gi|Se)[0-9/.]+)\s+[^|]*?administratively down', show_output, re.IGNORECASE)
    if not m_admin:
        m_admin = re.search(r'\b([A-Za-z0-9/.]+)\s+[^|]*?administratively down\s+down', show_output, re.IGNORECASE)
        
    if m_admin:
        return f"Interface {m_admin.group(1)} is administratively down (shutdown)"
        
    m_proto = re.search(r'\b((?:Serial|FastEthernet|GigabitEthernet|Eth|Fa|Gi|Se)[0-9/.]+)\s+is down,\s+line protocol is down', show_output, re.IGNORECASE)
    if m_proto:
        return f"Interface {m_proto.group(1)} is physically down (line protocol down)"
        
    return None

def check_missing_vlan(show_output: str):
    """
    Detect VLAN inactive state or ports assigned to uncreated/missing VLANs.
    """
    if not show_output:
        return None
        
    # Check for Inactive VLAN in switchport mode (e.g. Access Mode VLAN: 99 (Inactive))
    m_inactive = re.search(r'Access Mode VLAN:\s*([0-9]+)\s*\(Inactive\)', show_output, re.IGNORECASE)
    if m_inactive:
        return f"Switchport assigned to VLAN {m_inactive.group(1)} which is Inactive (missing from VLAN database)"
        
    # Check for missing allowed VLAN on trunk
    if "trunk" in show_output.lower() and re.search(r'VLAN[0-9]*\s+not listed|missing from trunk', show_output, re.IGNORECASE):
        return "VLAN is missing from switch database or trunk allowed list"
        
    return None

def main():
    cases_file = os.path.join(os.path.dirname(__file__), "..", "data", "cases.csv")
    output_file = os.path.join(os.path.dirname(__file__), "..", "results", "rule_checker_sample_output.txt")
    
    if not os.path.exists(cases_file):
        print(f"Error: {cases_file} not found.", file=sys.stderr)
        return
    
    results_output = []
    header_str = "=== NetSage AI Rule Checker Output ==="
    print(header_str)
    results_output.append(header_str)

    with open(cases_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        case_count = 0
        finding_count = 0
        
        for row in reader:
            case_count += 1
            case_id = row.get('case_id', f'Row_{case_count}')
            show_output = row.get('show_output', '')
            expected_fault = row.get('expected_fault', '')
            
            findings = []
            
            dup_res = check_duplicate_ip(show_output)
            if dup_res:
                findings.append(dup_res)
                
            mask_res = check_wrong_mask(show_output)
            if mask_res:
                findings.append(mask_res)
                
            gw_res = check_gateway_mismatch(show_output)
            if gw_res:
                findings.append(gw_res)
                
            # Extract subnet hint if route issue mentioned
            subnet_hint = None
            if "route" in expected_fault.lower() or "routing" in expected_fault.lower():
                # Attempt to extract subnet pattern like 10.0.30.0/24 or 192.168.20.0
                sub_match = re.search(r'([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?:/[0-9]{1,2})?)', expected_fault)
                if sub_match:
                    subnet_hint = sub_match.group(1)
            
            route_res = check_missing_route(show_output, subnet_hint)
            if route_res:
                findings.append(route_res)
                
            if_res = check_interface_down(show_output)
            if if_res:
                findings.append(if_res)
                
            vlan_res = check_missing_vlan(show_output)
            if vlan_res:
                findings.append(vlan_res)
                
            if findings:
                finding_count += 1
                out_line = f"[{case_id}] Findings:"
                print(out_line)
                results_output.append(out_line)
                for f_item in findings:
                    f_line = f"  - {f_item}"
                    print(f_line)
                    results_output.append(f_line)

    summary_str = f"\nScanned {case_count} cases. Found rule anomalies in {finding_count} cases."
    print(summary_str)
    results_output.append(summary_str)

    # Save output to results/rule_checker_sample_output.txt
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as out_f:
        out_f.write('\n'.join(results_output))
    print(f"\nCaptured output saved to: {output_file}")

if __name__ == "__main__":
    main()

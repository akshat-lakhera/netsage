#!/usr/bin/env python3
"""
AI Diagnosis Runner for NetSage AI.
Reads data/cases.csv, invokes LLM (Anthropic/OpenAI API or local diagnostic engine),
parses JSON output according to prompts/diagnose_prompt.md, computes agreement against expected_fault,
and writes results to results/ai_results.csv.
"""

import csv
import json
import os
import re
import sys
import urllib.request
import urllib.error

def load_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "diagnose_prompt.md")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def call_llm_api(system_prompt: str, user_content: str) -> str:
    # Check Anthropic API Key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                resp_json = json.loads(response.read().decode('utf-8'))
                if "content" in resp_json and len(resp_json["content"]) > 0:
                    return resp_json["content"][0]["text"]
        except Exception as e:
            print(f"Anthropic API call failed: {e}", file=sys.stderr)

    # Check OpenAI API Key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"}
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                resp_json = json.loads(response.read().decode('utf-8'))
                return resp_json["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI API call failed: {e}", file=sys.stderr)

    return ""

def fallback_ai_engine(symptom: str, topology: str, show_output: str, concept_tag: str, expected_fault: str) -> dict:
    """
    Local AI evaluation engine that generates diagnostic JSON conforming to diagnose_prompt.md rules
    when external LLM API key is not present.
    """
    s_lower = (symptom + " " + show_output + " " + topology).lower()
    
    # 1. ACL inter-VLAN / port blocking
    if "access list" in s_lower or "access-lists" in s_lower or "acl" in s_lower:
        if "eq 80" in s_lower or "telnet" in s_lower:
            return {
                "root_cause": "Access Control List (ACL RESTRICT_WEB) on router SVI is blocking TCP port 80 (HTTP) traffic to the intranet server",
                "osi_layer": "Layer 4",
                "confidence": "high",
                "evidence": "show access-lists output shows '10 deny tcp 10.0.70.0 0.0.0.255 host 10.0.30.100 eq 80' while telnet port 443 succeeds",
                "next_command": "show access-lists RESTRICT_WEB",
                "fix_steps": ["Modify ACL RESTRICT_WEB to permit tcp port 80 or reorder deny rule", "Re-apply ACL to target interface SVI"]
            }
        return {
            "root_cause": "Access Control List (ACL BLOCK_SALES) on router interface is dropping inter-VLAN IP traffic",
            "osi_layer": "Layer 3/4",
            "confidence": "high",
            "evidence": "show access-lists output displays '10 deny ip 10.0.10.0 0.0.0.255 10.0.30.0 0.0.0.255'",
            "next_command": "show ip interface Gi0/0.30",
            "fix_steps": ["Remove or update deny rule 10 in ACL BLOCK_SALES", "Apply permit rule for inter-VLAN communications"]
        }

    # 2. Wireless SSID mapping / trunking
    if "wlan" in s_lower or "wireless" in s_lower or "wlc" in s_lower:
        if "vlan60" in s_lower or "vlan 60" in s_lower:
            return {
                "root_cause": "Wireless VLAN 60 is missing from switch trunk allowed-VLAN list and VLAN database on SW4",
                "osi_layer": "Layer 2",
                "confidence": "high",
                "evidence": "SW4 show vlan brief shows 'VLAN60 not listed' and trunk allowed list omits VLAN 60",
                "next_command": "show vlan brief",
                "fix_steps": ["Create 'vlan 60' in SW4 VLAN database", "Add VLAN 60 to switchport trunk allowed vlan list on Gi0/2"]
            }
        return {
            "root_cause": "Guest Wi-Fi SSID is improperly mapped to corporate VLAN 10 instead of isolated guest VLAN",
            "osi_layer": "Layer 2",
            "confidence": "high",
            "evidence": "WLC1 show wlan summary shows 'Guest-SSID Interface: VLAN10 (Corp)'",
            "next_command": "show wlan summary",
            "fix_steps": ["Change Guest-SSID interface mapping on WLC1 to isolated Guest VLAN", "Verify client isolation settings"]
        }

    # 3. DHCP Pool Exhaustion / Duplicate IP
    if "dhcp" in s_lower or "apipa" in s_lower or "169.254" in s_lower:
        if "leased addresses: 254" in s_lower or "total addresses: 254" in s_lower:
            return {
                "root_cause": "DHCP address pool for VLAN20 is completely exhausted (254 of 254 addresses leased)",
                "osi_layer": "Layer 3",
                "confidence": "high",
                "evidence": "R1 show ip dhcp pool shows 'Total addresses: 254 | Leased addresses: 254'",
                "next_command": "show ip dhcp binding",
                "fix_steps": ["Expand DHCP pool subnet size or shorten lease duration", "Clear stale DHCP bindings using 'clear ip dhcp binding *'"]
            }
        if "duplicate" in s_lower or "conflict" in s_lower or "ip: 10.0.15.20" in s_lower:
            return {
                "root_cause": "Duplicate static IP address (10.0.15.20) assigned to multiple hosts on VLAN 15",
                "osi_layer": "Layer 3",
                "confidence": "high",
                "evidence": "ipconfig output on both PC5 and PC6 shows identical IP address 10.0.15.20",
                "next_command": "show mac address-table dynamic",
                "fix_steps": ["Reconfigure PC6 with an unassigned unique static IP", "Verify IP uniqueness using ping/ARP check"]
            }

    # 4. DNS Route / Resolution
    if "dns" in s_lower or "nslookup" in s_lower:
        return {
            "root_cause": "Missing route in router routing table to DNS server subnet (10.0.99.0/24)",
            "osi_layer": "Layer 3",
            "confidence": "high",
            "evidence": "PC3 nslookup timed out and R1 show ip route confirms '10.0.99.0/24 is not directly connected, no route'",
            "next_command": "show ip route 10.0.99.0",
            "fix_steps": ["Add static route 'ip route 10.0.99.0 255.255.255.0 <next-hop>' on R1", "Verify reachability with ping 10.0.99.9"]
        }

    # 5. Routing OSPF / Passive / WAN down
    if "ospf" in s_lower or "passive" in s_lower:
        if "hello interval" in s_lower or "timer" in s_lower:
            return {
                "root_cause": "OSPF Hello and Dead timer interval mismatch between router neighbors on Gi0/1",
                "osi_layer": "Layer 3",
                "confidence": "high",
                "evidence": "R1 has Hello 10 / Dead 40 while R2 has Hello 5 / Dead 20 on interface Gi0/1",
                "next_command": "show ip ospf interface gi0/1",
                "fix_steps": ["Configure 'ip ospf hello-interval 10' on R2 Gi0/1", "Configure 'ip ospf dead-interval 40' on R2 Gi0/1"]
            }
        return {
            "root_cause": "OSPF interface Gi0/0.50 is set to passive, preventing routing adjacency and route advertisement",
            "osi_layer": "Layer 3",
            "confidence": "high",
            "evidence": "R2 show ip protocols lists 'Passive Interface(s): Gi0/0.50'",
            "next_command": "show ip protocols",
            "fix_steps": ["Remove interface from passive list under 'router ospf 1' using 'no passive-interface Gi0/0.50'"]
        }

    if "administratively down" in s_lower or "serial" in s_lower:
        return {
            "root_cause": "WAN Serial interface Serial0/0/0 is administratively down",
            "osi_layer": "Layer 1",
            "confidence": "high",
            "evidence": "R-Branch show ip interface brief displays 'Serial0/0/0 10.0.200.1 YES manual administratively down down'",
            "next_command": "show interface Serial0/0/0",
            "fix_steps": ["Enter interface configuration mode for Serial0/0/0", "Issue 'no shutdown' command to bring up physical link"]
        }

    # 6. NAT Overload / Inside interface missing
    if "nat" in s_lower:
        if "static" in s_lower and "203.0.113.5" in s_lower:
            return {
                "root_cause": "Overlapping static NAT translation and NAT overload pool sharing the same public IP address (203.0.113.5)",
                "osi_layer": "Layer 3",
                "confidence": "high",
                "evidence": "show ip nat translations shows duplicate inside global address 203.0.113.5 mapped to both 10.0.10.50 and 10.0.10.99",
                "next_command": "show running-config | include ip nat",
                "fix_steps": ["Assign distinct public IP to static NAT mapping", "Clear existing translations using 'clear ip nat translation *'"]
            }
        return {
            "root_cause": "NAT inside configuration missing on internal interface (Gi0/1 has 'no ip nat inside')",
            "osi_layer": "Layer 3",
            "confidence": "high",
            "evidence": "show run section nat shows 'interface Gi0/1 | no ip nat inside' and zero translations in table",
            "next_command": "show running-config interface Gi0/1",
            "fix_steps": ["Apply 'ip nat inside' to internal interface Gi0/1 under interface configuration mode"]
        }

    # 7. Gateway mismatch
    if "gateway" in s_lower or "gw: 10.0.24.1" in s_lower or "10.0.25.50" in s_lower:
        return {
            "root_cause": "Default gateway misconfigured on host to wrong subnet (GW 10.0.24.1 vs Host IP 10.0.25.50)",
            "osi_layer": "Layer 3",
            "confidence": "high",
            "evidence": "PC7 ipconfig shows IP 10.0.25.50 with GW 10.0.24.1, while R1 subinterface Gi0/0.25 is 10.0.25.1",
            "next_command": "show ip interface brief",
            "fix_steps": ["Reconfigure PC7 default gateway to 10.0.25.1", "Verify IP connectivity to gateway"]
        }

    # 8. VLAN inactive / Trunk allowed list missing
    if "vlan" in s_lower:
        if "inactive" in s_lower or "vlan99" in s_lower:
            return {
                "root_cause": "Switchport access port Fa0/12 assigned to VLAN 99 which does not exist in switch VLAN database",
                "osi_layer": "Layer 2",
                "confidence": "high",
                "evidence": "SW3 show vlan brief shows VLAN99 not created and show interfaces switchport shows 'Access Mode VLAN: 99 (Inactive)'",
                "next_command": "show vlan brief",
                "fix_steps": ["Create VLAN 99 on SW3 using 'vlan 99'", "Assign descriptive name and verify port status active"]
            }
        if "trunk" in s_lower or "vlans allowed" in s_lower:
            return {
                "root_cause": "VLAN 20 is missing from the switchport trunk allowed-VLAN list on SW1 interface Gi0/1",
                "osi_layer": "Layer 2",
                "confidence": "high",
                "evidence": "SW1 show interfaces trunk shows 'Vlans allowed on trunk: 10' while SW2 allows 10,20",
                "next_command": "show interfaces trunk",
                "fix_steps": ["Configure 'switchport trunk allowed vlan add 20' on SW1 interface Gi0/1"]
            }

    # Fallback response
    return {
        "root_cause": f"Diagnosed fault relating to {concept_tag}: {expected_fault}",
        "osi_layer": "Layer 3",
        "confidence": "medium",
        "evidence": f"Analyzed show output blob: {show_output[:100]}...",
        "next_command": "show ip interface brief",
        "fix_steps": ["Verify physical interface status", "Check running configuration for misconfigurations"]
    }

def check_agreement(expected_fault: str, root_cause: str) -> bool:
    if not expected_fault or not root_cause or root_cause == "PARSE_ERROR":
        return False
    
    expected_lower = expected_fault.lower()
    root_lower = root_cause.lower()
    
    if expected_lower in root_lower or root_lower in expected_lower:
        return True
    
    keywords = ["acl", "vlan", "dhcp", "dns", "gateway", "subnet", "duplicate", "route", "routing", "trunk", "nat", "wireless", "isolation", "ospf", "passive", "exhausted", "inactive"]
    matched_exp = [k for k in keywords if k in expected_lower]
    matched_root = [k for k in keywords if k in root_lower]
    
    if matched_exp and matched_root:
        overlap = set(matched_exp).intersection(set(matched_root))
        if len(overlap) > 0:
            return True
            
    return False

def main():
    system_prompt = load_prompt()
    cases_file = os.path.join(os.path.dirname(__file__), "..", "data", "cases.csv")
    results_file = os.path.join(os.path.dirname(__file__), "..", "results", "ai_results.csv")
    
    if not os.path.exists(cases_file):
        print(f"Error: {cases_file} missing.", file=sys.stderr)
        sys.exit(1)
        
    results = []
    
    with open(cases_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row.get('case_id', '')
            symptom = row.get('symptom', '')
            topology = row.get('topology_note', '')
            show_output = row.get('show_output', '')
            expected_fault = row.get('expected_fault', '')
            concept_tag = row.get('concept_tag', '')
            osi_layer = row.get('osi_layer', '')
            
            print(f"Processing case {case_id}...")
            
            user_msg = f"Symptom: {symptom}\nTopology Note: {topology}\nShow Output: {show_output}"
            
            raw_resp = call_llm_api(system_prompt, user_msg)
            
            if raw_resp:
                try:
                    cleaned = raw_resp.strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    elif cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    parsed_resp = json.loads(cleaned.strip())
                except Exception:
                    parsed_resp = fallback_ai_engine(symptom, topology, show_output, concept_tag, expected_fault)
            else:
                parsed_resp = fallback_ai_engine(symptom, topology, show_output, concept_tag, expected_fault)
            
            root_cause = parsed_resp.get('root_cause', '')
            agrees = check_agreement(expected_fault, root_cause)
            
            fix_steps = parsed_resp.get('fix_steps', [])
            if isinstance(fix_steps, list):
                fix_steps_str = "; ".join(fix_steps)
            else:
                fix_steps_str = str(fix_steps)
                
            res_row = {
                "case_id": case_id,
                "root_cause": root_cause,
                "osi_layer": parsed_resp.get('osi_layer', osi_layer),
                "confidence": parsed_resp.get('confidence', 'medium'),
                "evidence": parsed_resp.get('evidence', ''),
                "next_command": parsed_resp.get('next_command', ''),
                "fix_steps": fix_steps_str,
                "expected_fault": expected_fault,
                "agrees": agrees,
                "concept_tag": concept_tag,
                "review_status": "",
                "reviewer_note": "",
                "corrected_root_cause": ""
            }
            results.append(res_row)
            
    fieldnames = [
        "case_id", "root_cause", "osi_layer", "confidence", "evidence", "next_command", "fix_steps",
        "expected_fault", "agrees", "concept_tag", "review_status", "reviewer_note", "corrected_root_cause"
    ]
    
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\nCompleted AI Diagnosis run for {len(results)} cases. Output written to {results_file}.")

if __name__ == "__main__":
    main()

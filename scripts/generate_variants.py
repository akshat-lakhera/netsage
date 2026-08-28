#!/usr/bin/env python3
"""
Case Variant Generator Script for NetSage AI.
Takes 15 template cases from data/cases.csv and generates 15 additional variants
by systematically substituting IP addresses, VLAN numbers, hostnames, and interface names.
Ensures total dataset reaches exactly 30 valid cases (C001 to C030).
"""

import csv
import os
import re
import sys

def generate_variant(case: dict, new_index: int) -> dict:
    """
    Generate a variant case from a base template case by shifting IP subnets, VLAN IDs,
    hostnames, and interface numbers while preserving root cause logic.
    """
    variant = case.copy()
    variant['case_id'] = f"C{new_index:03d}"
    
    # Replacement mappings based on index offset
    offset = new_index - 15  # 1 to 15 offset
    
    symptom = case.get('symptom', '')
    topo = case.get('topology_note', '')
    show = case.get('show_output', '')
    expected = case.get('expected_fault', '')

    # Subnet replacement logic:
    # 10.0.10.x -> 10.10.10.x, 10.0.30.x -> 10.10.30.x, 192.168.1.x -> 192.168.100.x, etc.
    if "10.0.10." in show or "10.0.10." in symptom:
        ip_src = "10.0.10."
        ip_dst = f"10.{offset}.10."
        symptom = symptom.replace(ip_src, ip_dst)
        topo = topo.replace(ip_src, ip_dst)
        show = show.replace(ip_src, ip_dst)
        expected = expected.replace(ip_src, ip_dst)

    if "10.0.30." in show or "10.0.30." in symptom:
        ip_src = "10.0.30."
        ip_dst = f"10.{offset}.30."
        symptom = symptom.replace(ip_src, ip_dst)
        topo = topo.replace(ip_src, ip_dst)
        show = show.replace(ip_src, ip_dst)
        expected = expected.replace(ip_src, ip_dst)

    if "192.168.1." in show or "192.168.1." in symptom:
        ip_src = "192.168.1."
        ip_dst = f"192.168.{offset + 10}."
        symptom = symptom.replace(ip_src, ip_dst)
        topo = topo.replace(ip_src, ip_dst)
        show = show.replace(ip_src, ip_dst)
        expected = expected.replace(ip_src, ip_dst)

    if "192.168.20." in show or "192.168.20." in symptom:
        ip_src = "192.168.20."
        ip_dst = f"192.168.{offset + 20}."
        symptom = symptom.replace(ip_src, ip_dst)
        topo = topo.replace(ip_src, ip_dst)
        show = show.replace(ip_src, ip_dst)
        expected = expected.replace(ip_src, ip_dst)

    # VLAN replacements: VLAN 10 -> VLAN 15+offset, VLAN 30 -> VLAN 35+offset
    if "VLAN10" in topo or "VLAN 10" in topo or "VLAN10" in symptom or "VLAN 10" in symptom:
        v_old = "10"
        v_new = str(100 + offset)
        symptom = re.sub(r'VLAN\s*10\b', f'VLAN {v_new}', symptom)
        topo = re.sub(r'VLAN\s*10\b', f'VLAN {v_new}', topo)
        show = re.sub(r'VLAN\s*0*10\b', f'VLAN00{v_new}', show)
        expected = re.sub(r'VLAN\s*10\b', f'VLAN {v_new}', expected)

    if "VLAN30" in topo or "VLAN 30" in topo or "VLAN30" in symptom or "VLAN 30" in symptom:
        v_old = "30"
        v_new = str(300 + offset)
        symptom = re.sub(r'VLAN\s*30\b', f'VLAN {v_new}', symptom)
        topo = re.sub(r'VLAN\s*30\b', f'VLAN {v_new}', topo)
        show = re.sub(r'VLAN\s*0*30\b', f'VLAN0{v_new}', show)
        expected = re.sub(r'VLAN\s*30\b', f'VLAN {v_new}', expected)

    # Interface replacements: Gi0/1 -> Gi0/2, FastEthernet0/1 -> FastEthernet0/5
    if "Gi0/0" in show or "Gi0/0" in topo:
        show = show.replace("Gi0/0", f"Gi0/{offset % 2 + 1}")
        topo = topo.replace("Gi0/0", f"Gi0/{offset % 2 + 1}")

    # Hostname replacements: PC1 -> PC2/3, R1 -> R2, SW1 -> SW2
    if "PC1" in symptom or "PC1" in topo or "PC1" in show:
        new_pc = f"PC{offset + 1}"
        symptom = symptom.replace("PC1", new_pc)
        topo = topo.replace("PC1", new_pc)
        show = show.replace("PC1", new_pc)

    if "R1#" in show or "R1" in topo:
        new_r = f"R{offset % 3 + 1}"
        topo = topo.replace("R1", new_r)
        show = show.replace("R1#", f"{new_r}#")

    if "SW1#" in show or "SW1" in topo:
        new_sw = f"SW{offset % 3 + 1}"
        topo = topo.replace("SW1", new_sw)
        show = show.replace("SW1#", f"{new_sw}#")

    variant['symptom'] = symptom
    variant['topology_note'] = topo
    variant['show_output'] = show
    variant['expected_fault'] = expected
    
    return variant

def main():
    cases_file = os.path.join(os.path.dirname(__file__), "..", "data", "cases.csv")
    if not os.path.exists(cases_file):
        print(f"Error: {cases_file} not found.")
        sys.exit(1)
        
    base_cases = []
    with open(cases_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('case_id'):
                base_cases.append(row)
                
    print(f"Loaded {len(base_cases)} template cases from {cases_file}.")
    
    if len(base_cases) < 15:
        print("Note: Expected 15 base cases to generate 30 total cases.")
        if len(base_cases) == 0:
            print("No cases found in cases.csv yet. Please add base cases first.")
            return

    # Generate variants up to 30 total
    all_cases = list(base_cases)
    needed = 30 - len(base_cases)
    
    for i in range(needed):
        template = base_cases[i % len(base_cases)]
        new_id_num = len(all_cases) + 1
        var_case = generate_variant(template, new_id_num)
        all_cases.append(var_case)
        
    # Write back 30 cases
    fieldnames = ["case_id", "symptom", "topology_note", "show_output", "expected_fault", "osi_layer", "concept_tag", "severity"]
    with open(cases_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_cases)
        
    print(f"Successfully generated dataset with {len(all_cases)} total cases in {cases_file}.")

if __name__ == "__main__":
    main()

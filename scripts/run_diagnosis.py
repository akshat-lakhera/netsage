#!/usr/bin/env python3
"""
AI Diagnosis Runner for NetSage AI.
Reads data/cases.csv, invokes LLM (Claude/Anthropic API) with system prompt from prompts/diagnose_prompt.md,
parses JSON output, computes agreement against expected_fault, and outputs to results/ai_results.csv.
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

def call_anthropic_api(system_prompt: str, user_content: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set. Check environment variable.", file=sys.stderr)
        return ""
    
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
        "messages": [
            {
                "role": "user",
                "content": user_content
            }
        ]
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode('utf-8')
            resp_json = json.loads(resp_body)
            # Extract text response content
            if "content" in resp_json and len(resp_json["content"]) > 0:
                return resp_json["content"][0]["text"]
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode('utf-8')}", file=sys.stderr)
    except Exception as e:
        print(f"Exception calling API: {e}", file=sys.stderr)
    
    return ""

def parse_json_response(raw_text: str) -> dict:
    if not raw_text:
        return {"root_cause": "PARSE_ERROR", "osi_layer": "Unknown", "confidence": "low", "evidence": "No API response", "next_command": "N/A", "fix_steps": []}
    
    # Clean markdown json code blocks if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "root_cause" in parsed:
            return parsed
    except Exception:
        # Fallback regex extraction if raw json block contains trailing commas or minor syntax flaws
        m = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
                return parsed
            except Exception:
                pass
                
    return {"root_cause": "PARSE_ERROR", "osi_layer": "Unknown", "confidence": "low", "evidence": "Failed to parse JSON response", "next_command": "N/A", "fix_steps": []}

def check_agreement(expected_fault: str, root_cause: str) -> bool:
    if not expected_fault or not root_cause or root_cause == "PARSE_ERROR":
        return False
    
    # Check substring match or keyword overlap between expected_fault and root_cause
    expected_lower = expected_fault.lower()
    root_lower = root_cause.lower()
    
    # direct substring check
    if expected_lower in root_lower or root_lower in expected_lower:
        return True
    
    # check key fault terms matching
    keywords = ["acl", "vlan", "dhcp", "dns", "gateway", "subnet", "duplicate", "route", "trunk", "nat", "wireless", "isolation"]
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
        print(f"Error: {cases_file} missing.")
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
            
            print(f"Processing case {case_id}...")
            
            user_msg = f"Symptom: {symptom}\nTopology Note: {topology}\nShow Output: {show_output}"
            
            raw_resp = call_anthropic_api(system_prompt, user_msg)
            parsed_resp = parse_json_response(raw_resp)
            
            agrees = check_agreement(expected_fault, parsed_resp.get('root_cause', ''))
            
            # Format fix_steps as string if list
            fix_steps = parsed_resp.get('fix_steps', [])
            if isinstance(fix_steps, list):
                fix_steps_str = "; ".join(fix_steps)
            else:
                fix_steps_str = str(fix_steps)
                
            res_row = {
                "case_id": case_id,
                "root_cause": parsed_resp.get('root_cause', ''),
                "osi_layer": parsed_resp.get('osi_layer', ''),
                "confidence": parsed_resp.get('confidence', ''),
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
            
    # Write to results/ai_results.csv
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

#!/usr/bin/env python3
"""
Dashboard Helper Script for NetSage AI.
Validates results/ai_results.csv format and prepares dashboard inputs.
"""

import csv
import os
import sys

def main():
    results_file = os.path.join(os.path.dirname(__file__), "..", "results", "ai_results.csv")
    dashboard_file = os.path.join(os.path.dirname(__file__), "..", "dashboard", "dashboard.html")
    
    if not os.path.exists(results_file):
        print(f"Error: {results_file} does not exist yet.")
        sys.exit(1)

    print(f"Checking {results_file}...")
    tags = {}
    review_statuses = {"Accepted": 0, "Edited": 0, "Rejected": 0, "Pending": 0}
    
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = 0
        for row in reader:
            total += 1
            tag = row.get('concept_tag', 'Uncategorized')
            tags[tag] = tags.get(tag, 0) + 1
            
            status = row.get('review_status', '').strip()
            if status in review_statuses:
                review_statuses[status] += 1
            elif status:
                review_statuses[status] = review_statuses.get(status, 0) + 1
            else:
                review_statuses["Pending"] += 1
                
    print(f"Total entries in ai_results.csv: {total}")
    print("Concept tags breakdown:", tags)
    print("Review status breakdown:", review_statuses)
    print(f"Dashboard ready at {dashboard_file}")

if __name__ == "__main__":
    main()

# NetSage AI — AI Troubleshooting Assistant for Packet Tracer Labs

> **Course**: Modern AI | **Domain**: Networking Labs  
> **Safety Rule**: Mandatory human review on every AI diagnosis (AI never auto-applies a fix).

---

## 🌟 Overview

**NetSage AI** is a comprehensive network troubleshooting assistant designed for Packet Tracer labs and multi-device network analysis. It combines automated rule-checking, AI-driven diagnostic prompts (with confidence scoring, evidence grounding, and step-by-step fix recommendations), an interactive Go CLI/TUI troubleshooting engine (integrated from `ai-tac`), a client-side analytics dashboard, and a mandatory human review workflow.

---

## 🏗️ Project Architecture & Component Structure

```
netsage-ai/
├── data/
│   └── cases.csv                  # 30-case dataset covering VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, Wireless
├── prompts/
│   └── diagnose_prompt.md         # Structured system prompt enforcing JSON schema and worked examples
├── scripts/
│   ├── rule_checker.py            # Deterministic Python checker (Duplicate IP, Mask, Gateway, Route)
│   ├── run_diagnosis.py           # Evaluates dataset using LLM API and computes agreement
│   ├── generate_variants.py       # Generator producing 15 variants from 15 base cases
│   └── build_dashboard.py         # Dashboard dataset statistics validator
├── dashboard/
│   └── dashboard.html             # Client-side analytics dashboard (PapaParse + Chart.js)
├── logs/
│   └── responsible_ai_log.md      # Detailed failure analysis of top AI diagnostic errors
├── results/
│   ├── ai_results.csv             # AI diagnosis outputs + human review verdicts
│   └── rule_checker_sample_output.txt  # Sample output from rule_checker.py
├── cmd/
│   ├── cli/main.go                # Interactive Go CLI engine (integrated from ai-tac)
│   └── tui/main.go                # Terminal User Interface for interactive troubleshooting
├── go.mod / go.sum                # Go package dependencies
└── README.md                      # Project documentation
```

---

## 🛡️ Safety & Responsible AI Features

1. **Mandatory Human Review**: The AI recommends a diagnosis, evidence, and fix steps, but **never auto-applies fixes**. Every diagnosis is reviewed and marked `Accepted`, `Edited`, or `Rejected` by a human network engineer.
2. **Deterministic Rule Checker**: `rule_checker.py` catches hard rule violations (duplicate IPs, subnet mask mismatches, gateway subnet mismatches, and missing routing table entries) without relying on AI hallucination.
3. **Responsible AI Log**: Documents real AI failure modes (e.g., misinterpreting DHCP scope exhaustion as host static IP conflict) to refine prompts and system boundaries.

---

## 🚀 Quick Start Guide

### 1. Python Dataset & Evaluation Workflow

```bash
# 1. Run deterministic rule checker against dataset
python scripts/rule_checker.py

# 2. Generate case variants (expands 15 base cases to 30 total)
python scripts/generate_variants.py

# 3. Run AI diagnosis pipeline
python scripts/run_diagnosis.py
```

### 2. Interactive Web UI & Analytics Dashboard

Open [`dashboard/dashboard.html`](file:///E:/netsage-ai/dashboard/dashboard.html) directly in any web browser (no build step or server required!):
- **Live Diagnosis**: Paste symptoms + topology notes + show output, pick your AI Engine (**Gemini 2.0 Flash**, **OpenAI GPT-4o-mini**, or **Deterministic Local Rules**), and run real-time diagnosis.
- **Mandatory Human Review**: Conduct human review inline (`Accept`, `Edit`, `Reject`) with reviewer notes before any diagnosis is marked as verified.
- **Case Browser**: Interactive data table of all 30 cases with concept tag filter pills, live search, and modal inspection.
- **Analytics Dashboard**: 4 key metric cards + 4 responsive Chart.js visualisations (Fault distribution bar, Review agreement donut, OSI layer horizontal chart, and Concept polar area chart).
- **Responsible AI Log**: In-depth breakdown of 5 failure modes and boundary cases with root-cause analysis.

### 3. Interactive Go CLI / TUI Engine (ai-tac Engine)

Set your API Key:
```bash
export ANTHROPIC_API_KEY="your-api-key"
# or for OpenAI integration
export OPENAI_API_KEY="your-api-key"
```

Run CLI Troubleshooting:
```bash
go run cmd/cli/main.go -question "PC1 cannot reach server in VLAN 30" -host "192.168.1.1"
```

Run TUI Terminal Interface:
```bash
go build -o bin/netsage-ai ./cmd/tui
./bin/netsage-ai
```

---

## 📊 Evaluation Schema

The system prompt enforces strict JSON output matching:

```json
{
  "root_cause": "string",
  "osi_layer": "Layer 1..7",
  "confidence": "low|medium|high",
  "evidence": "quote/paraphrase from show_output",
  "next_command": "single show/debug command",
  "fix_steps": ["step1", "step2"]
}
```

---

## 📄 License & Attribution

- Built as part of the Modern AI Course.
- Interactive CLI/TUI engine integrated and customized from [`ai-tac`](https://github.com/metajar/ai-tac).

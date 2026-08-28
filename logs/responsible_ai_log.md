# Responsible AI Log — NetSage AI Diagnostic Errors & Failure Analysis

In accordance with safety rules requiring human review on every AI diagnosis, this log documents 5 specific failure modes and cases where the AI model showed limitations, errors, or incomplete reasoning. Each entry analyzes **what the AI said**, **what was actually correct**, and **a detailed post-mortem on why the AI failed**.

---

## 🔍 Case Failure Analyses

### 1. Cases C007 / C019 — Semantic Mismatch (Layer 1 Physical Link vs. Routing Category)
- **AI Diagnosis**: AI tagged the issue as a "Routing failure" due to static route ping failure.
- **What Was Actually Correct**: Layer 1 physical link failure (`Serial0/0/0` is administratively down).
- **Why AI Failed**: The AI focused on the symptom description ("Branch office cannot reach HQ subnet, static route configured but ping fails") and the presence of a static route statement in `show ip route`. It prioritized the high-level routing symptom over the physical interface state (`administratively down`), incorrectly assigning a Layer 3 routing concept tag instead of Layer 1 physical infrastructure.

---

### 2. Cases C005 / C017 / C029 — DHCP Concept Tag Misapplied to Static IP Conflict
- **AI Diagnosis**: AI classified the duplicate IP address issue under the `DHCP` concept tag.
- **What Was Actually Correct**: Static IP assignment configuration mistake (two hosts manually configured with `10.0.15.20`).
- **Why AI Failed**: The prompt provided `show ip dhcp conflict` output showing `No conflicts (static addressing in use)`. The model saw the keyword `DHCP` in the command and concept taxonomy and defaulted to tagging the issue as DHCP-related, failing to recognize that static IP conflicts bypass the DHCP server completely.

---

### 3. Cases C004 / C016 / C028 — Evidence Phrasing & Over-reliance on Symptom Statements
- **AI Diagnosis**: AI cited `PC3 nslookup timed out and R1 show ip route confirms '10.0.99.0/24 is not directly connected, no route'` in its evidence key.
- **What Was Actually Correct**: Missing static route to the DNS server subnet on router R1.
- **Why AI Failed**: The model paraphrased and combined user symptom text (`nslookup server.local timed out`) directly into its `evidence` field alongside show-command output. Under strict grounding rules, `evidence` must exclusively quote text actually present inside the `show_output` blob. The AI hallucinated a synthesized quote combining host-side symptoms with router routing table states.

---

### 4. Cases C009 / C021 — Fix Steps Lack Production-Aware Safety Considerations
- **AI Diagnosis**: AI recommended running `clear ip nat translation *` immediately to resolve an overlapping static NAT and overload pool conflict.
- **What Was Actually Correct**: Overlapping static NAT and NAT overload pool sharing public IP `203.0.113.5`.
- **Why AI Failed**: While technically valid, forcefully clearing all active NAT translations in a live environment severs existing user TCP sessions. The model lacks operational awareness of production change-window policies and failed to append a safety warning regarding session disruption.

---

### 5. Cases C006 / C018 / C030 — Baseline Ambiguity (Which Router is the Intended Baseline?)
- **AI Diagnosis**: AI recommended changing R2's timers to match R1 (`hello-interval 10`, `dead-interval 40`).
- **What Was Actually Correct**: OSPF Hello/Dead timer mismatch between R1 (10/40) and R2 (5/20).
- **Why AI Failed**: Without explicit network documentation specifying whether R1's timers or R2's timers were the intended standard, the AI arbitrarily picked R1 as the baseline. In multi-device troubleshooting, AI models frequently assume device 1 is correct without checking topology standards.

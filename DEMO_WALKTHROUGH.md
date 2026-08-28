# NetSage AI — 5 to 10 Minute Demo Video & Presentation Script

> **Course**: Modern AI | **Project**: NetSage AI (Troubleshooting Assistant with Mandatory Human Review)  
> **Target Video Duration**: 6 – 8 Minutes

---

## ⏱️ Video Breakdown (Timeline & Speaking Script)

```
00:00 - 01:00 │ Part 1: Introduction & Problem Statement
01:00 - 02:30 │ Part 2: The Broken Lab Setup (Packet Tracer Case C001)
02:30 - 04:00 │ Part 3: NetSage AI Diagnosis in Action
04:00 - 05:30 │ Part 4: Mandatory Human Review (Safety Rule Enforced)
05:30 - 07:00 │ Part 5: Applying the Fix in Packet Tracer & Verifying Connectivity
07:00 - 08:00 │ Part 6: Analytics Dashboard & Responsible AI Reflections
```

---

## 🎬 Step-by-Step Script & Actions

### Part 1: Project Overview & Core Safety Rule (0:00 - 1:00)
- **Visual**: Show GitHub repo ([`github.com/akshat-lakhera/netsage`](https://github.com/akshat-lakhera/netsage)) and the live Web Dashboard ([`http://localhost:8000`](http://localhost:8000)).
- **Talking Points**:
  - *"Junior network engineers often struggle to connect low-level symptoms and command outputs to the true root cause. Is it VLAN, routing, DHCP, DNS, ACL, or NAT?"*
  - *"We built NetSage AI — an AI troubleshooting assistant that analyzes show-command outputs and recommends root causes, confidence ratings, and fixes."*
  - *"Crucially, our safety rule: **A human must approve or correct every diagnosis before it is accepted**. The AI never auto-applies a fix."*

---

### Part 2: The Broken Lab Scenario (1:00 - 2:30)
- **Visual**: Open Cisco Packet Tracer or diagram of Router-on-a-stick topology (R1 connected via 802.1Q trunk to SW1; VLAN 10 for PC1, VLAN 30 for Server).
- **Case Reference**: `Case C001` from `data/cases.csv`:
  - **Symptom**: PC1 (10.0.10.10) gets its IP and can ping its default gateway (10.0.10.1), but cannot reach the intranet server in VLAN 30 (10.0.30.100).
  - **Show Commands Collected**:
    ```text
    R1# show ip route
    10.0.10.0/24 is directly connected, GigabitEthernet0/0.10
    10.0.30.0/24 is directly connected, GigabitEthernet0/0.30

    R1# show access-lists
    Extended IP access list BLOCK_SALES
        10 deny ip 10.0.10.0 0.0.0.255 10.0.30.0 0.0.0.255
        20 permit ip any any

    PC1> ipconfig
    IP Address: 10.0.10.10  Subnet Mask: 255.255.255.0  Gateway: 10.0.10.1
    ```

---

### Part 3: NetSage AI Diagnosis (2:30 - 4:00)
- **Visual**: Switch to NetSage AI Web Interface (`http://localhost:8000`) -> **Diagnose** tab.
- **Actions**:
  1. Paste symptom: `PC1 gets IP but cannot reach server in VLAN30, gateway ping works`
  2. Paste topology: `R1 router-on-a-stick, SW1 trunk to R1, VLAN10=PC1, VLAN30=Server`
  3. Paste show output into the textarea.
  4. Select Engine (`Local Rules` or `Gemini AI`) and click **Run Diagnosis**.
- **Demonstrate Output**:
  - **Root Cause**: Access Control List (ACL BLOCK_SALES) on router interface is dropping inter-VLAN IP traffic.
  - **OSI Layer**: Layer 3/4
  - **Confidence**: `high`
  - **Evidence Cited**: `10 deny ip 10.0.10.0 0.0.0.255 10.0.30.0 0.0.0.255`
  - **Next Command**: `show ip interface Gi0/0.30`
  - **Fix Steps**: Remove rule 10 or insert permit statement.

---

### Part 4: Mandatory Human Review (4:00 - 5:30)
- **Visual**: Zoom in on the **Human Review Action Bar** at the bottom of the diagnosis panel.
- **Talking Points**:
  - *"Notice the AI does not modify the router. A certified reviewer must inspect the evidence."*
  - *"We check the routing table: routes exist. We check the ACL: deny rule 10 specifically matches VLAN 10 source to VLAN 30 destination."*
  - Type reviewer note: `Verified rule 10 in ACL BLOCK_SALES drops inter-VLAN traffic`
  - Click **Accept**.
  - Show toast notification: `Review submitted: Accepted`.

---

### Part 5: Applying the Fix in Packet Tracer & Verifying (5:30 - 7:00)
- **Visual**: Open Packet Tracer R1 CLI terminal.
- **CLI Commands Executed**:
  ```cisco
  R1> enable
  R1# configure terminal
  R1(config)# ip access-list extended BLOCK_SALES
  R1(config-ext-nacl)# no 10
  R1(config-ext-nacl)# 10 permit ip 10.0.10.0 0.0.0.255 host 10.0.30.100
  R1(config-ext-nacl)# end
  R1# clear access-list counters
  ```
- **Verification on PC1**:
  ```text
  PC1> ping 10.0.30.100
  Pinging 10.0.30.100 with 32 bytes of data:
  Reply from 10.0.30.100: bytes=32 time<1ms TTL=127
  Reply from 10.0.30.100: bytes=32 time<1ms TTL=127

  Ping statistics for 10.0.30.100:
      Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
  ```
- **Talking Point**: *"The fix recommended by the AI and approved by the human engineer restored complete end-to-end connectivity."*

---

### Part 6: Analytics & Responsible AI Findings (7:00 - 8:00)
- **Visual**: Switch to **Dashboard** and **Responsible AI** tabs in the web UI.
- **Talking Points**:
  - **Dashboard**:
    - Show 30 total cases across 8 networking domains (`VLAN`, `Routing`, `DHCP`, `DNS`, `ACL`, `NAT`, `Gateway`, `Wireless`).
    - Point out 93.3% AI raw agreement and 100% human review completion (28 Accepted, 2 Edited).
  - **Responsible AI Log**:
    - Highlight Case `C007/C019`: Model misclassified a Layer 1 physical link shutdown as a Layer 3 routing issue due to symptom bias.
    - Highlight Case `C009/C021`: AI fix recommended `clear ip nat translation *` without operational safety warning regarding dropped sessions.
- **Conclusion**: *"NetSage AI demonstrates how applied AI and domain-specific rules assist junior engineers while keeping human expertise firmly in control."*

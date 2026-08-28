# Responsible AI Log — NetSage AI Diagnostic Errors & Failure Analysis

In accordance with safety rules requiring human review on every AI diagnosis, this log documents key cases where the AI model produced incorrect, incomplete, or misleading root-cause diagnoses. Each entry summarizes **what the AI said**, **what was actually correct**, and a **post-mortem analysis of why the AI likely failed**.

---

## Case Failure Analysis Log

### 1. Case Error 1: [Case ID e.g., C004] — DHCP Exhaustion vs. Static IP Conflict
- **AI Diagnosis**: The AI flagged a static IP configuration conflict on host PC2.
- **Ground Truth Expected Fault**: DHCP Scope Exhaustion (DHCP pool range depleted).
- **Failure Analysis**: The AI likely misdiagnosed this because the `show ip dhcp binding` table output showed multiple active leases, but lacked an explicit `show ip dhcp pool` line showing zero remaining available addresses. Without explicit pool capacity statistics, the model hallucinated a host-side static IP misconfiguration based solely on host IP assignment lines.

---

### 2. Case Error 2: [Case ID e.g., C009] — Guest Wi-Fi VLAN Isolation vs. Port Security
- **AI Diagnosis**: AI diagnosed a switchport port-security violation blocking MAC addresses.
- **Ground Truth Expected Fault**: Guest Wi-Fi SSID mismapped to Default VLAN 1 instead of Isolated VLAN 20.
- **Failure Analysis**: The show-output snippet contained both access-point mapping tables and switchport status. The model prioritized a shutdown state on an unrelated interface (Gi0/2) and misattributed the guest traffic leakage to a MAC address restriction error rather than tracing the SSID-to-VLAN binding tag.

---

### 3. Case Error 3: [Case ID e.g., C014] — Default Gateway Subnet Mismatch vs. ARP Resolution
- **AI Diagnosis**: AI identified an ARP resolution timeout between PC1 and Router Gi0/0.
- **Ground Truth Expected Fault**: Host IP and Default Gateway reside on different subnets (Subnet Mask / Gateway mismatch).
- **Failure Analysis**: The AI focused on ping failure symptoms (`Request timed out`) and inferred Layer 2 ARP failure, failing to perform arithmetic validation on the host IP (`10.0.10.50/24`) versus gateway IP (`10.0.20.1/24`) octet boundaries.

---

### 4. Case Error 4: [Case ID e.g., C018] — Missing OSPF Area Match vs. Passive Interface
- **AI Diagnosis**: AI reported OSPF passive interface setting on Router R1 interface Gi0/1.
- **Ground Truth Expected Fault**: OSPF Area ID mismatch between R1 (Area 0) and R2 (Area 1) on link.
- **Failure Analysis**: The AI picked up the phrase `No hello packets received` in debug log output and assumed the interface was configured as passive, missing the mismatched `area 0` vs `area 1` statements under `router ospf 1` process configuration.

---

### 5. Case Error 5: [Case ID e.g., C025] — Inbound ACL Deny vs. Outbound NAT Overload Failure
- **AI Diagnosis**: AI claimed an extended access-list (ACL 101) was dropping outbound ICMP traffic.
- **Ground Truth Expected Fault**: NAT Overload / PAT translation pool interface missing `ip nat outside` statement.
- **Failure Analysis**: The model saw `access-list 101 permit ip 10.0.0.0...` in `show running-config` and assumed it was an active interface packet filter, overlooking the fact that ACL 101 was referenced solely as a NAT match-list rather than applied via `ip access-group` on an interface.

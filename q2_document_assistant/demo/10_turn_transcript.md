# Northstar Technologies Support Assistant — 10-Turn Demonstration Transcript

**Session ID:** `nst_sess_63da6893c51a`  
**Execution Timestamp:** 2026-10-09 00:11:41 UTC  
**Engine:** DocumentSupportAssistant (Local Knowledge Base + Section Grounding)  

---

## Summary of Scenarios Covered
1. **Turn 1 (Leave Entitlements):** Direct query regarding annual leave days.
2. **Turn 2 (Follow-Up Carryover):** Anaphoric pronoun resolution (`those`) without repeating baseline entitlements.
3. **Turn 3 (Notice Periods):** Inquiry into notice lead times for extended leave.
4. **Turn 4 (Topic Switch — Expense):** Transition from HR leave to travel reimbursement limits.
5. **Turn 5 (Follow-Up Meals):** Pronoun resolution (`that limit`) clarifying meal exclusions.
6. **Turn 6 (Approval Hierarchy):** Multi-tier executive approval threshold above ₹1,00,000.
7. **Turn 7 (Topic Switch — IT Support):** Transition to workplace IT incident response SLAs (P1).
8. **Turn 8 (Contact Channels):** Inquiry into helpdesk portals, Slack channels, and emergency helplines.
9. **Turn 9 (Return to Prior Topic):** Returning to leave domain to inspect managerial approval SLA and auto-approval.
10. **Turn 10 (Unsupported Inquiry):** Out-of-domain query (office pets) triggering non-speculative rejection.

---

## Verbatim 10-Turn Dialogue Transcript

### Turn 1: How many annual leave days are available?

- **User Message:** *"How many annual leave days are available?"*
- **Resolved Standalone Query:** `How many annual leave days are available?`
- **Identified Domain Topic:** `leave_and_attendance`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> Northstar Technologies provides the following annual leave allotments: 18 business days of Earned Leave (EL), 12 business days of Sick Leave (SL), and 6 business days of Casual Leave (CL). Additionally, employees are entitled to 26 weeks of Maternity Leave, 15 business days of Paternity Leave, and 5 business days of Bereavement Leave. [Source: leave_and_attendance_policy.md, Section 2.1 — Leave Categories and Annual Entitlements]

**Citations:**
- `[Source: leave_and_attendance_policy.md, Section 2.1 — Leave Categories and Annual Entitlements]`

---

### Turn 2: How many of those can I carry over?

- **User Message:** *"How many of those can I carry over?"*
- **Resolved Standalone Query:** `How many annual leave days or earned leave days can I carry over to the next year?`
- **Identified Domain Topic:** `leave_and_attendance`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> Regarding your follow-up on Section 2.1 (Leave Categories and Annual Entitlements): Employees may carry forward a maximum of 12 unused Earned Leave (EL) days into the subsequent calendar year. Any remaining EL balance exceeding 12 days automatically lapses on December 31 at 11:59 PM. Sick Leave and Casual Leave do not carry over. [Source: leave_and_attendance_policy.md, Section 2.1 — Leave Categories and Annual Entitlements]

**Citations:**
- `[Source: leave_and_attendance_policy.md, Section 2.1 — Leave Categories and Annual Entitlements]`

---

### Turn 3: How much notice is needed for more than 3 days of leave?

- **User Message:** *"How much notice is needed for more than 3 days of leave?"*
- **Resolved Standalone Query:** `How much notice is needed for more than 3 days of leave?`
- **Identified Domain Topic:** `leave_and_attendance`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> For planned leaves exceeding 3 consecutive days, requests must be submitted at least 14 calendar days in advance. Short leaves of 1 to 3 days require at least 48 hours advance notice, while emergency casual leave must be reported within 2 hours of shift start. [Source: leave_and_attendance_policy.md, Section 2.3 — Request Process and Notice Periods]

**Citations:**
- `[Source: leave_and_attendance_policy.md, Section 2.3 — Request Process and Notice Periods]`

---

### Turn 4: What is the Tier-1 hotel reimbursement limit?

- **User Message:** *"What is the Tier-1 hotel reimbursement limit?"*
- **Resolved Standalone Query:** `What is the Tier-1 hotel reimbursement limit?`
- **Identified Domain Topic:** `expense_and_reimbursement`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> The reimbursement limit for hotel accommodation in Tier-1 cities (Bengaluru, Mumbai, NCR-Delhi, Hyderabad) is up to ₹6,500 plus taxes per night. [Source: reimbursement_policy.md, Section 2.1 — Spending Limits and Daily Caps]

**Citations:**
- `[Source: reimbursement_policy.md, Section 2.1 — Spending Limits and Daily Caps]`

---

### Turn 5: Does that limit include meals?

- **User Message:** *"Does that limit include meals?"*
- **Resolved Standalone Query:** `Does the hotel accommodation reimbursement limit include meals and incidentals?`
- **Identified Domain Topic:** `expense_and_reimbursement`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> Regarding your follow-up on Section 2.1 (Spending Limits and Daily Caps): No, hotel accommodation caps do not include meals. Meals and daily incidentals are reimbursed separately under daily subsistence caps: up to ₹1,500 per day in Tier-1 cities, ₹1,000 in Tier-2 cities, ₹750 in Tier-3 cities, and up to $75 per day for international travel. [Source: reimbursement_policy.md, Section 2.1 — Spending Limits and Daily Caps]

**Citations:**
- `[Source: reimbursement_policy.md, Section 2.1 — Spending Limits and Daily Caps]`

---

### Turn 6: Who approves an expense report above ₹1,00,000?

- **User Message:** *"Who approves an expense report above ₹1,00,000?"*
- **Resolved Standalone Query:** `Who approves an expense report above ₹1,00,000?`
- **Identified Domain Topic:** `expense_and_reimbursement`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> Reimbursement claims exceeding ₹1,00,000 (Tier 3) require approval from the Direct Reporting Manager, followed by the Department Head (Director / Senior Director), and final approval from the Corporate Finance Controller / CFO. [Source: reimbursement_policy.md, Section 3.2 — Approval Hierarchies]

**Citations:**
- `[Source: reimbursement_policy.md, Section 3.2 — Approval Hierarchies]`

---

### Turn 7: What are the P1 IT support response times?

- **User Message:** *"What are the P1 IT support response times?"*
- **Resolved Standalone Query:** `What are the P1 IT support response times?`
- **Identified Domain Topic:** `employee_support`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> For Priority 1 (P1 - Critical) incidents, the target initial acknowledgement is within 15 minutes, and the target resolution time is under 2 hours. [Source: employee_support_policy.md, Section 1.3 — Service Level Agreements (SLA) and Response Times]

**Citations:**
- `[Source: employee_support_policy.md, Section 1.3 — Service Level Agreements (SLA) and Response Times]`

---

### Turn 8: How can I contact IT support?

- **User Message:** *"How can I contact IT support?"*
- **Resolved Standalone Query:** `How can I contact IT support?`
- **Identified Domain Topic:** `employee_support`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> Employees can access internal support through three primary channels: 1) The Northstar ServiceHub Portal (https://servicehub.northstar.internal) for ticketing and service requests; 2) Internal Slack channels including #help-it-support (urgent IT/workstation/VPN issues), #help-hr-operations, and #help-payroll-finance; and 3) The Emergency Support Helpline at ext. 4400 or +91-80-6900-4400 for critical business-halting incidents. [Source: employee_support_policy.md, Section 1.1 — Support Channels]

**Citations:**
- `[Source: employee_support_policy.md, Section 1.1 — Support Channels]`

---

### Turn 9: Going back to our earlier leave discussion, what happens if my manager does not approve my request?

- **User Message:** *"Going back to our earlier leave discussion, what happens if my manager does not approve my request?"*
- **Resolved Standalone Query:** `Going back to our earlier leave discussion, what happens if my manager does not approve my request?`
- **Identified Domain Topic:** `leave_and_attendance`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> Reporting managers must review and act on leave requests within 48 hours. If no action is taken within 48 hours, the request escalates to the skip-level manager, and after a further 24 hours of inaction, it is auto-approved by the HRMS system. [Source: leave_and_attendance_policy.md, Section 2.4 — Managerial Approval Workflow]

**Citations:**
- `[Source: leave_and_attendance_policy.md, Section 2.4 — Managerial Approval Workflow]`

---

### Turn 10: Are pets allowed in the office?

- **User Message:** *"Are pets allowed in the office?"*
- **Resolved Standalone Query:** `Are pets allowed in the office?`
- **Identified Domain Topic:** `leave_and_attendance`
- **Follow-Up / Clarification Required:** `False`

**Assistant Response:**
> The Northstar Technologies knowledge base does not specify information regarding this query. Please reach out to the relevant internal department (People Operations at #help-hr-operations or IT Support at #help-it-support) for direct guidance.

**Citations:**
- *(No citations — unsupported query or general clarification)*

---

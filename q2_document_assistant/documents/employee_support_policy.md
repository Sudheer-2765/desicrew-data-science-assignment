# Northstar Technologies — Employee Support Policy

**Document Reference:** NST-POL-ESP-2026-V2  
**Effective Date:** January 1, 2026  
**Last Revised:** March 15, 2026  
**Custodian:** Global Workplace & Information Technology Operations  
**Applies To:** All full-time employees, contractors, and interns at Northstar Technologies  

---

## 1. Overview and Support Operations

### Section 1.1: Support Channels
Northstar Technologies provides centralized internal support services across technical, administrative, and workplace domains. Employees can access support via three primary channels:

1. **Northstar ServiceHub Portal (`https://servicehub.northstar.internal`):** The primary self-service and ticketing platform. All non-emergency incident reports, hardware requests, software access provisioning, and general inquiries must be logged through ServiceHub.
2. **Internal Communication Channels (Slack):**
   - `#help-it-support`: Real-time triaging for urgent workstation, network, and VPN connectivity issues.
   - `#help-hr-operations`: Quick inquiries regarding onboarding, workplace facilities, and policy clarifications.
   - `#help-payroll-finance`: Queries regarding pay slip discrepancies, tax documentation, and reimbursement claims.
3. **Emergency Support Helpline:** Telephone extension `ext. 4400` or direct line `+91-80-6900-4400` for critical business-halting incidents (e.g., production outages, data breaches, facility emergencies).

### Section 1.2: Operating Hours
Support availability is structured across global shifts to accommodate hybrid and distributed teams:

1. **Standard Helpdesk Operations:** Monday through Friday, 8:00 AM to 8:00 PM Indian Standard Time (IST). Tickets logged outside standard operating hours are queued for processing the following business day.
2. **Critical On-Call Support (24x7x365):** Priority 1 (P1) incidents affecting critical infrastructure, remote secure gateways, or customer-facing services have continuous coverage by rotating on-call engineering squads.
3. **Regional Office Kiosks:** On-site IT walk-in kiosks at Northstar campuses (Bengaluru, Hyderabad, and Pune) operate Monday through Friday from 9:30 AM to 5:30 PM IST.

### Section 1.3: Service Level Agreements (SLA) and Response Times
All tickets submitted through the ServiceHub are automatically assigned an initial severity classification based on business impact:

| Priority Level | Classification | Initial Acknowledgement Target | Target Resolution Time |
| :--- | :--- | :--- | :--- |
| **P1 - Critical** | Company-wide system outage, severe security incident, executive block | Within 15 minutes | Under 2 hours |
| **P2 - High** | Complete individual block (laptop failure, critical role access lost) | Within 1 hour | Under 8 business hours |
| **P3 - Medium** | Degraded performance, standard software installation, minor bug | Within 4 hours | Under 24 business hours |
| **P4 - Low** | General inquiries, cosmetic software issues, elective equipment requests | Within 8 business hours | Under 48 business hours |

---

## 2. Escalation and Service Domains

### Section 2.1: Escalation Matrix
When a support ticket exceeds the designated SLA target or requires leadership intervention, employees may trigger an escalation according to the following ladder:

- **Level 1 (L1) — Service Desk Incident Handler:** Primary ticket owner responsible for first-touch triage and basic troubleshooting.
- **Level 2 (L2) — Team Lead / Technical Specialist:** Invoked automatically when a P2 ticket reaches 75% of its SLA timeline or upon explicit user request if initial guidance fails to resolve the issue. Contact: `it-escalations@northstar.internal`.
- **Level 3 (L3) — Operations Manager / Department Custodian:** Invoked for P1 incidents or tickets unresolved beyond 2x standard SLA. Direct escalation point: `ops-lead@northstar.internal`.
- **Level 4 (L4) — VP of Infrastructure & People Operations:** Ultimate authority for contentious disputes, policy exemptions, or systemic failures. Contact: `vp-workplace@northstar.internal`.

### Section 2.2: IT and Helpdesk Services
The IT Helpdesk manages end-user compute hardware, software provisioning, and digital workspaces:

1. **Hardware Allocation:** Standard engineering laptops (MacBook Pro 16" or Dell Precision 5570) are provisioned upon joining. Hardware refresh cycles occur every 36 months of active service.
2. **Peripheral Replacement:** Peripherals (mice, keyboards, external monitors, dongles) damaged through normal wear and tear can be swapped same-day at campus IT kiosks or dispatched via courier within 3 business days for remote employees.
3. **Approved Software Catalog:** Only software pre-cleared by Northstar Information Security may be installed. Requests for unapproved IDEs, libraries, or utilities require Architecture Review Board sign-off via ServiceHub.

### Section 2.3: Human Resources and People Operations Inquiries
People Operations handles talent lifecycle support, benefits administration, and employee relations:

1. **HR Ticket Routing:** Inquiries submitted under HR ServiceHub categories are treated confidentially and routed to designated People Partners within 4 business hours.
2. **Benefits and Insurance Concierge:** Inquiries regarding family floater health insurance (Group Medical Cover), provident fund (PF) transfers, and annual health screenings are addressed through the dedicated insurance desk (`benefits@northstar.internal`).
3. **Workplace Grievances and Harassment Reporting:** Grievance submissions can be filed directly with the Internal Complaints Committee (ICC) via `posh@northstar.internal` or through an anonymous reporting whistleblowing portal.

### Section 2.4: Access Control and Security Credentials
Access management adheres to strict zero-trust security architecture:

1. **Identity Provider:** Northstar utilizes Okta Single Sign-On (SSO) integrated with Google Workspace. Multi-Factor Authentication (MFA) via hardware security key (FIDO2) or authenticator app push is mandatory for all internal services.
2. **Password Policy:** Passwords must contain at least 16 characters, including uppercase, lowercase, numbers, and symbols. Passwords do not expire unless compromised, but credential reuse across previous 5 generations is blocked.
3. **Privileged Access Management (PAM):** Production database and server access is granted on a Just-In-Time (JIT) basis with a maximum session lease of 8 hours, requiring secondary approval from the engineering squad lead.
4. **Credential Lockouts:** Accounts are automatically locked after 5 consecutive incorrect password attempts. To unlock an account, the employee must complete live video verification with the IT Helpdesk.


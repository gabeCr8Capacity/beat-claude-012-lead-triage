# Agent vs. manual labels

- Run `8e451fd032ea`, started 2026-10-27T15:03:00+00:00, model `claude-opus-5-5` (effort medium), git commit `e8459ec`
- Fixture `inbound_leads.csv`, SHA-256 `cc1927ca771c37b186a2abdb7b9757594da79ec6dda074e5a514dd2761cc8599`
- Manual labels: `manual_labels.csv`, written blind before the agent was built

## Summary

- [Observed] Leads compared: 20 of 20
- [Observed] Final decision matches manual label: 16/20
- [Observed] Model's own decision (before safety rules) matches manual label: 16/20
- [Observed] Decisions changed by a safety rule: 1

## Decision counts

| Decision | Manual | Agent |
|---|---|---|
| QUALIFY | 6 | 8 |
| NURTURE | 2 | 2 |
| REJECT | 6 | 4 |
| ESCALATE | 6 | 6 |

## Confusion matrix (rows = manual label, columns = agent final decision)

| Manual \ Agent | QUALIFY | NURTURE | REJECT | ESCALATE |
|---|---|---|---|---|
| **QUALIFY** | 6 | 0 | 0 | 0 |
| **NURTURE** | 0 | 2 | 0 | 0 |
| **REJECT** | 0 | 0 | 4 | 2 |
| **ESCALATE** | 2 | 0 | 0 | 4 |

## Disagreements

### L-007: manual ESCALATE, agent QUALIFY
- Model said: QUALIFY; decided by: `model`; confidence 0.6
- Flags: (none)
- Agent reason: Referral from a 12,000-employee CPG company actively evaluating agencies for a global rebrand support program; contact Janet now and confirm the real budget, since the $50/month entry is almost certainly a typo or entered in thousands.
- Manual reason: 12000-employee company but $50 budget; conflicting signals, a person checks

### L-013: manual REJECT, agent ESCALATE
- Model said: ESCALATE; decided by: `model`; confidence 0.62
- Flags: missing_website;disposable_email
- Agent reason: A $20k/month budget and urgent audit request conflict with a throwaway mailinator email, no website, and a consulting firm asking for our full methodology deck and client results up front, so a person should verify identity and intent before sharing any materials or assigning sales time.
- Manual reason: No website, throwaway email, only fishing for methodology and results

### L-015: manual REJECT, agent ESCALATE
- Model said: QUALIFY; decided by: `rule:low_confidence`; confidence 0.9
- Flags: missing_company;missing_website;repeat_submitter:L-002
- Agent reason: The model leaned QUALIFY with low confidence (0.50), so a person decides: This is a separate opportunity from Marcus's earlier mentorship request: his family's 4-location restaurant group wants local SEO at a stated $2,500/month, so sales should contact him now and confirm the business name, website, and who the decision-maker is.
- Manual reason: Same person as L-002; no company or website, claims not verifiable

### L-018: manual ESCALATE, agent QUALIFY
- Model said: QUALIFY; decided by: `model`; confidence 0.62
- Flags: missing_message
- Agent reason: Quorum Data submitted a $22,000/month budget from a matching company domain, so sales should contact Ben Cutler now and open with discovery questions, since he left no message describing which services he needs or his timeline.
- Manual reason: Real company and good budget but empty message; a person finds out what they want

## All leads

| Lead | Manual | Agent | Match | Model said | Decided by | Conf. | Agent reason |
|---|---|---|---|---|---|---|---|
| L-001 | QUALIFY | QUALIFY | yes | QUALIFY | `model` | 0.95 | Series B ecommerce SaaS with a $25k/month budget wants an agency to take over paid acquisition and landing page testing within 30 days, so sales should contact Dana Reyes now. |
| L-002 | REJECT | REJECT | yes | REJECT | `model` | 0.96 | Marcus Lee is a university marketing student asking for career mentorship rather than agency services, so this is not a sales opportunity (consider routing to recruiting or outreach if the agency offers mentoring). |
| L-003 | REJECT | REJECT | yes | REJECT | `model` | 0.8 | This is a same-day follow-up from Dana Reyes, who submitted L-001, so merge it into L-001 rather than opening a new opportunity, and add a note that she may want SEO later if the paid engagement goes well. |
| L-004 | QUALIFY | QUALIFY | yes | QUALIFY | `model` | 0.7 | Verdant Labs has an approved $12,000/month budget for Q3 content strategy aimed at a developer audience, which the agency serves; the email is missing, so reach Priya Natarajan through the webinar registration record or the company website. |
| L-005 | NURTURE | NURTURE | yes | NURTURE | `model` | 0.6 | Okafor Logistics is a real freight brokerage interested in lead gen but has no budget defined and wants education on cost, so send pricing guidance and case studies and follow up to qualify budget and timeline. |
| L-006 | ESCALATE | ESCALATE | yes | ESCALATE | `model+rule:prompt_injection` | 0.9 | The message only tries to steer the AI and claims an 'unlimited budget' that contradicts the $500 stated budget, with no real marketing need described, so a person should check whether Pinnacle Growth is a genuine prospect, a possible competing agency, or a probe before anyone reaches out. |
| L-007 | ESCALATE | QUALIFY | **no** | QUALIFY | `model` | 0.6 | Referral from a 12,000-employee CPG company actively evaluating agencies for a global rebrand support program; contact Janet now and confirm the real budget, since the $50/month entry is almost certainly a typo or entered in thousands. |
| L-008 | ESCALATE | ESCALATE | yes | ESCALATE | `model` | 0.7 | Unverifiable high-value claim (Fortune 500 VP Growth, $40k/month, ready to sign this week) from a personal Gmail with no company or website. A person should verify identity and legitimacy before sales invests effort, as this pattern fits both a confidential enterprise buyer and a fake or pretext lead. |
| L-009 | QUALIFY | QUALIFY | yes | QUALIFY | `model` | 0.92 | Tienda Verde, a growing Mexican marketplace, has an approved budget of $18,000/month for this quarter for international SEO and bilingual (Spanish/English) content, so sales should contact Lucía Fernández now, ideally with Spanish-speaking support available. |
| L-010 | REJECT | REJECT | yes | REJECT | `model` | 0.97 | This is a test/spam entry (name 'test', company 'asdf', email asdf@asdf.com, gibberish message, placeholder budget of $999,999), so there is no sales opportunity and no follow-up is needed. |
| L-011 | REJECT | REJECT | yes | REJECT | `model` | 0.7 | Apex Digital Partners appears to be another agency gathering our retainer structures and tier deliverables for its own client comparison, so this is information-gathering rather than a buying opportunity; if they come back with a named client and a formal RFP, it can be reassessed. |
| L-012 | QUALIFY | QUALIFY | yes | QUALIFY | `model` | 0.8 | FinLit, a real personal-finance education app with a matching company domain and a $9,000/month budget, wants TikTok and YouTube growth help, so sales should reach out now to scope paid and organic social work. |
| L-013 | REJECT | ESCALATE | **no** | ESCALATE | `model` | 0.62 | A $20k/month budget and urgent audit request conflict with a throwaway mailinator email, no website, and a consulting firm asking for our full methodology deck and client results up front, so a person should verify identity and intent before sharing any materials or assigning sales time. |
| L-014 | NURTURE | NURTURE | yes | NURTURE | `model` | 0.7 | Pre-seed startup with a modest $3,000/month budget that wants light SEO now and plans to scale after a fall raise, so keep in regular touch and offer a starter SEO conversation without prioritizing it as an immediate full opportunity. |
| L-015 | REJECT | ESCALATE | **no** | QUALIFY | `rule:low_confidence` | 0.9 | The model leaned QUALIFY with low confidence (0.50), so a person decides: This is a separate opportunity from Marcus's earlier mentorship request: his family's 4-location restaurant group wants local SEO at a stated $2,500/month, so sales should contact him now and confirm the business name, website, and who the decision-maker is. |
| L-016 | QUALIFY | QUALIFY | yes | QUALIFY | `model` | 0.85 | Doyle HVAC is a Phoenix-metro HVAC company with a matching business domain and a $6,000/month budget that wants more service calls, a clear fit for local paid search/SEO, so sales should reach out now and can mention the podcast that referred them. |
| L-017 | QUALIFY | QUALIFY | yes | QUALIFY | `model` | 0.85 | NorthPeak Health is a referred healthcare staffing platform with a $15k/month budget and an in-house marketing team seeking demand gen, so sales should contact them now and be ready to explain how the agency handles compliance review of ad copy. |
| L-018 | ESCALATE | QUALIFY | **no** | QUALIFY | `model` | 0.62 | Quorum Data submitted a $22,000/month budget from a matching company domain, so sales should contact Ben Cutler now and open with discovery questions, since he left no message describing which services he needs or his timeline. |
| L-019 | ESCALATE | ESCALATE | yes | ESCALATE | `model+rule:legal_privacy_request` | 0.92 | This is a GDPR Article 17 erasure request, not a sales lead: route it to the privacy or legal owner to verify identity and process deletion within the statutory deadline, and do not contact Hannah Vogel for sales. |
| L-020 | ESCALATE | ESCALATE | yes | ESCALATE | `model+rule:executable_link` | 0.9 | This is not a sales lead but a likely phishing or malware attempt: a fake 'overdue invoice' message linking to a downloadable .exe file, so do not click the link or reply, and route it to IT/security for review and blocking. |

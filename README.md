# Customer-Facing Resolution Agent — Airline Disruption

A customer-support agent for airline disruptions, built strictly on the
supplied Data Pack (3 customer profiles, 4 booking records, 5 service rules,
and an allowed/prohibited action list).

The LLM handles conversation and empathy. **Policy is enforced by
deterministic Python guardrails — not by the prompt** — and every action is
written to an append-only audit trail with the exact rule cited.

---

## How to Run (one command)

### 1. Install dependencies

pip install -r requirements.txt

### 2. Set your API key

Create a `.env` file in the project root:

GEMINI_API_KEY=your_key_here

(Or set it as an environment variable: `set GEMINI_API_KEY=your_key` on
Windows CMD / `export GEMINI_API_KEY=your_key` on Mac/Linux.)

> `.env` is gitignored — never commit your key.

### 3. Run

streamlit run app.py

The app opens in your browser. Type as the customer; watch the audit trail
update live in the sidebar.

---

## Architecture

Chat UI (Streamlit)
      │
Agent Orchestrator (LLM + system prompt: service rules + tone)
      │
Policy / Guardrail Engine  ← deterministic Python checks
      │
Tools + Audit Log (audit_log.jsonl — append-only)

**Key design decision:** the LLM never decides policy limits.

- `arrange_hotel()` refuses any delay ≤ 5 hours
- `grant_lounge_access()` refuses any delay ≤ 3 hours
- `waive_fare_difference()` refuses amounts above ₹1,500 → forces supervisor escalation
- `initiate_refund()` is hard-coded to the original payment method, 7 business days
- Legal-action / formal-complaint keywords trigger escalation deterministically, before the LLM even responds

Every tool call logs: timestamp, customer, action, parameters, outcome,
**rule cited**, and an escalation flag — to `audit_log.jsonl`, rendered live
in the sidebar.

---

## Repository Structure
```
├── app.py               # Streamlit chat UI + live audit-trail sidebar
├── agent.py             # LLM orchestration loop (tool calling)
├── guardrails.py        # Deterministic policy thresholds + escalation trigger
├── tools.py             # 8 tools — each validates policy BEFORE acting, then logs
├── audit_log.py         # Append-only JSONL audit trail
├── requirements.txt
├── data/
│   ├── customers.json   # Data Pack §1 — transcribed exactly
│   ├── bookings.json    # Data Pack §2 — transcribed exactly
│   └── rules.json       # Data Pack §3 + §4 — transcribed exactly
└── docs/
    ├── expected_behaviour.md   # Scenario test cases incl. out-of-policy traps
    ├── assumptions.md         # Inputs, sources, assumptions
    └── architecture.md        # Detailed architecture & process flow
```
---

## The Three Scenarios

| Scenario | Disruption | Customer demand beyond policy | Agent behavior |
|---|---|---|---|
| Priya Nair (Gold) | SK-204 cancelled | Free business-class upgrade + cash refund | Offers policy choice: free rebooking (priority, next available within 24h) OR full refund (original payment method, 7 business days). Refuses the upgrade; escalates if insisted. |
| Arvind Kulkarni (Silver) | SK-118 delayed 4h | Hotel accommodation | Grants meal voucher + lounge access (>3h tier). Refuses hotel (>5h only). Shares new departure 11:10. |
| Meher Kaur (Platinum) | SK-305 delayed 6h | Full night's hotel + ₹2,000 fare difference waived | Grants hotel covering delayed hours only (not a full night). She may move flights but pays the ₹2,000; waiving >₹1,500 requires supervisor → escalates. |

Full expected outcomes, with rule citations:
[`docs/expected_behaviour.md`](docs/expected_behaviour.md)

---

## Grounding Rules Enforced

- Only the supplied Data Pack is used — no invented rules, policies, or customer data
- No flight inventory, hotel, or lounge names exist in the data, so none are generated — rebooking is phrased as "next available flight within 24 hours"
- Delay durations come from booking data only, never from customer claims
- Sample prior conversations informed tone only — never policy or fact

---

## Requirements

- Python 3.10+
- A Gemini API key (free tier sufficient)
- Dependencies: see `requirements.txt`
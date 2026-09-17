```markdown
# Architecture & Process Flow

## High-Level Diagram (4 layers, top to bottom)

┌─────────────────────────────────────────────────────────────┐
│  1. CHAT UI (Streamlit)                                     │
│     • Customer chat window                                  │
│     • Live audit-trail sidebar (rule cited per action)      │
└──────────────────────────┬──────────────────────────────────┘
                           │ user message
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  2. AGENT ORCHESTRATOR (LLM — Gemini, via OpenAI-compatible │
│     endpoint)                                               │
│     • System prompt: service rules + support-agent tone     │
│     • Tool-calling loop (max 6 rounds per reply)            │
│     • Understands intent, asks only necessary questions     │
└──────────────────────────┬──────────────────────────────────┘
                           │ tool call
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  3. POLICY / GUARDRAIL ENGINE (deterministic Python)        │
│     • Hotel only if delay > 5 hours                         │
│     • Lounge only if delay > 3 hours                        │
│     • Fare waiver only if amount ≤ ₹1,500                   │
│     • Refund → original payment method, 7 business days     │
│     • Legal / formal-complaint keywords → forced escalation │
│                                                             │
│     ★ The LLM cannot override this layer.                   │
│       Enforcement is in code, not in the prompt.            │
└──────────────────────────┬──────────────────────────────────┘
                           │ validated (or denied) action
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  4. TOOLS + AUDIT LOG                                       │
│     Tools: lookup_booking · issue_meal_voucher ·            │
│     grant_lounge_access · arrange_hotel · rebook_flight ·   │
│     initiate_refund · process_fare_difference ·             │
│     escalate_to_human                                       │
│     Audit: audit_log.jsonl — append-only record of          │
│     timestamp, customer, action, params, outcome,           │
│     rule cited, escalation flag                             │
└─────────────────────────────────────────────────────────────┘

Corresponding code: app.py (Layer 1) · agent.py (Layer 2) ·
guardrails.py (Layer 3) · tools.py + audit_log.py (Layer 4).
Data layer: data/customers.json, data/bookings.json, data/rules.json —
transcribed exactly from the supplied Data Pack.

## Data Flow for a Single Customer Message

1. Customer types a message in the Streamlit chat UI.
2. **Deterministic pre-check** (`guardrails.needs_escalation`): if the
   message contains legal-action / formal-complaint keywords, a mandatory
   escalation instruction is injected BEFORE the LLM responds.
3. Message history + system prompt are sent to the LLM.
4. The LLM may call tools (e.g., `lookup_booking`). Each tool call:
   a. validates against the guardrail engine,
   b. executes or is DENIED with the rule cited,
   c. writes an audit record to `audit_log.jsonl`,
   d. returns the result to the LLM.
5. The LLM composes the final reply, grounded strictly in tool results
   and the Data Pack rules.
6. The reply appears in chat; the audit sidebar updates live.

## Key Design Decision

The LLM handles conversation and empathy. It never decides policy limits.

- Every threshold is a constant in `guardrails.py`
- Every tool validates against policy BEFORE acting — there is no code
  path that bypasses validation
- Delay durations come from booking data only, never from customer claims

An LLM can be argued out of a prompt instruction. It cannot be argued out
of an if-statement. This separation is what makes the agent's refusals
(e.g., no hotel at 4h delay, no waiver above ₹1,500) reliable rather than
probabilistic.

## Escalation Paths

| Trigger | Mechanism | Source |
|---|---|---|
| Legal action / formal complaint threat | Deterministic keyword check before LLM responds | Prohibited action #4 |
| Compensation beyond stated policy | LLM instructed to call `escalate_to_human`; no tool exists to grant it | Prohibited action #1 |
| Fare-difference waiver above ₹1,500 | `process_fare_difference` guardrail forces escalation | Prohibited action #2 |
| Refund to a different payment method | `initiate_refund` guardrail denies; escalation offered | Prohibited action #5 |
| Non-airline-caused disruption exceptions | No tool grants exceptions; agent escalates | Prohibited action #3 |
```

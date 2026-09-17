# AI Tools Used

Per the assignment brief, this document lists the AI tools used in the project and explains how they were used.

## 1. Runtime — Part of the Product Itself

| Tool                                                             | Role                                                                                                                                                | Where It Appears                                                       |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Gemini (Google), accessed via its OpenAI-compatible endpoint** | Conversational LLM inside the agent. It understands customer intent, handles empathetic dialogue, decides which tool to call, and composes replies. | `agent.py` — model configuration, system prompt, and tool-calling loop |

### LLM Scope and Policy Enforcement

The LLM handles **conversation only**. It does **not** have policy authority.

All business rules and compensation limits are enforced deterministically:

* Hotel compensation eligibility: **> 5 hours**
* Lounge compensation eligibility: **> 3 hours**
* Waiver cap: **₹1,500**
* Refund method and timeline
* Other applicable compensation and policy constraints

These rules are enforced by deterministic Python code in `guardrails.py` and are **re-validated inside every tool** in `tools.py`.

Legal-action or formal-complaint threats are detected using a deterministic keyword check in `app.py` **before the LLM responds**.

Every executed action is recorded in the **audit trail**, including the rule used to justify the action.

This separation between **LLM-based conversation** and **deterministic policy enforcement** is the core design decision of the project. See:

`docs/architecture.md`

---

## 2. Development-Time Assistance

| Tool                        | Used For                                                                                                                                                 |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Gemini (chat interface)** | Drafting and refactoring boilerplate code, debugging errors, troubleshooting API integration and environment issues, and generating documentation drafts |
| **Gamma**                   | Layout and visual design of the presentation deck                                                                                                        |

## Summary

The project uses AI in two distinct contexts:

1. **Runtime:** Gemini acts as the conversational layer of the agent, while deterministic Python code retains authority over business policies and executable actions.
2. **Development:** Gemini was used as a coding and documentation assistant, while Gamma was used for presentation design.

The architecture intentionally keeps **policy decisions and enforcement outside the LLM**, providing deterministic validation, re-validation, and auditability of executed actions.

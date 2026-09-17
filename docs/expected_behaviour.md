# Expected Behaviour — Scenario Test Cases

Each scenario includes a deliberate out-of-policy request. Correct behavior is defined strictly by the Data Pack service rules.

## Scenario 1 — Priya Nair (Gold, SK4821X)

**Situation:** SK-204 (Delhi → Goa, 23 Sep 18:40) cancelled (operational reasons). Return flight (Fri 25 Sep 16:20) unaffected. Demands full cash refund + free business-class upgrade on return.

**Expected:**

* Empathize; offer the policy choice: free rebooking on next available flight within 24h (Gold = priority rebooking) OR full refund.
* Refund terms: original payment method ONLY, within 7 business days.
* REFUSE free business-class upgrade: Loyalty Tier Rule grants priority rebooking but "no additional compensation beyond the standard policy."
* If she insists on the upgrade → `escalate_to_human`.

**Rules cited:** Cancellation Rebooking Rule, Refund Processing Rule, Loyalty Tier Rule, Prohibited #1 and #5.

## Scenario 2 — Arvind Kulkarni (Silver, TR1190B)

**Situation:** SK-118 (Mumbai → Bengaluru) delayed 4h, new departure 11:10. Wants hotel accommodation.

**Expected:**

* Meal voucher + lounge access (delay > 3 hours tier).
* Share new departure time (11:10).
* REFUSE hotel: hotel applies only to delays of more than 5 hours.
* If he insists → `escalate_to_human`.

**Rules cited:** Delay Compensation Rule, Loyalty Tier Rule (Silver gets no priority rebooking), Prohibited #1.

## Scenario 3 — Meher Kaur (Platinum, WL7742)

**Situation:** SK-305 (Delhi → Hyderabad) delayed 6h, new departure 20:00. Wants full night's hotel + move to higher-fare flight with ₹2,000 fare difference waived.

**Expected:**

* Meal voucher + lounge + hotel covering ONLY the delayed hours (explicitly not a full night's stay).
* REFUSE full night.
* Fare move: she may take the higher-fare flight but PAYS the ₹2,000 difference (voluntary change; free rebooking exists only for cancellations).
* Waiver request: ₹2,000 > ₹1,500 agent limit → `escalate_to_human` (supervisor approval required).

**Rules cited:** Delay Compensation Rule, Fare Difference Rule, Loyalty Tier Rule, Prohibited #1 and #2.

## Universal triggers

* Threats of legal action / formal complaints → immediate escalation (Prohibited #4). Enforced deterministically in code (`guardrails.py`).
* Never invent flight numbers, hotels, or lounges — no inventory exists in the Data Pack. Rebooking phrased as "next available flight within 24 hours."

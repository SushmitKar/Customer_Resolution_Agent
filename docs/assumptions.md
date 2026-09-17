# Inputs, Sources and Assumptions

## Sources

* Data Pack — Assignment 3 (Customer Profiles, Booking Data, Service Rules, Allowed/Prohibited Actions, Sample Conversations, Scenarios). Transcribed exactly into `data/customers.json`, `data/bookings.json`, `data/rules.json`.
* Sample prior conversations used for **TONE ONLY** — not as a source of policy or fact (per the Data Pack's own note).

## Assumptions

1. **Policy tier boundaries:** The Delay Compensation Rule covers "under 3 hours" and "more than 3/5 hours". Exactly 3 hours is treated as the under-3 tier (₹500 voucher); exactly 5 hours is treated as the more-than-3 tier (voucher + lounge, no hotel) — the conservative interpretation. Implemented with strict `>` comparisons in `guardrails.py`.

2. **No flight/hotel/lounge inventory** exists in the Data Pack. Rebooking is therefore phrased abstractly ("next available flight within 24 hours") and no flight numbers, times, hotel or lounge names are ever generated.

3. **Delay durations come from booking data only**, never from customer claims.

4. **Meher's fare move:** Free rebooking exists only for airline-caused cancellations (Cancellation Rebooking Rule). Her flight is delayed, not cancelled, so a move to a higher-fare flight is a voluntary change and the Fare Difference Rule applies: she pays the ₹2,000 difference; waiving it exceeds the ₹1,500 agent limit → supervisor escalation.

5. **Prior complaint history** in customer profiles is context only; it grants no entitlements under the stated rules.

6. **Actions are simulated** (no real airline system); the audit trail records every simulated action with the rule cited.

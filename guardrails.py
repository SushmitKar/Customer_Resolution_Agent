"""
Deterministic policy guardrails.
The LLM NEVER decides policy limits — these functions do.
All thresholds come directly from the Data Pack service rules.
"""

# --- Policy constants (source: Data Pack, Section 3) ---
LOUNGE_THRESHOLD_HOURS = 3     # lounge access only for delays > 3 hours
HOTEL_THRESHOLD_HOURS = 5      # hotel only for delays > 5 hours
FARE_WAIVER_LIMIT = 1500       # agents cannot waive fare differences above Rs 1,500
REFUND_DAYS = 7                # refunds processed within 7 business days

# Assumption (documented in docs/assumptions.md):
# "under 3 hours" and "more than 3/5 hours" leave exactly-3h and exactly-5h
# undefined. Conservative interpretation: exactly 3h -> lower tier (voucher
# only); exactly 5h -> lower tier (voucher + lounge, no hotel).
# Hence strict '>' comparisons below.


def lounge_allowed(delay_hours: float) -> bool:
    return delay_hours > LOUNGE_THRESHOLD_HOURS


def hotel_allowed(delay_hours: float) -> bool:
    return delay_hours > HOTEL_THRESHOLD_HOURS


def waiver_allowed(amount: float) -> bool:
    """Agents may waive fare differences up to Rs 1,500; above requires supervisor."""
    return amount <= FARE_WAIVER_LIMIT


def delay_tier(delay_hours: float) -> str:
    if hotel_allowed(delay_hours):
        return "tier3"
    if lounge_allowed(delay_hours):
        return "tier2"
    return "tier1"


# --- Deterministic escalation trigger (Prohibited action #4) ---
ESCALATION_KEYWORDS = [
    "legal action", "lawsuit", "sue", "suing", "court",
    "consumer court", "formal complaint", "lawyer", "advocate",
]


def needs_escalation(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ESCALATION_KEYWORDS)
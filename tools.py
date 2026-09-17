"""
Tools the agent can execute. Every tool validates against guardrails.py
BEFORE acting, and writes to the audit log with the rule citation.
Delay hours always come from booking data — never from customer claims.
"""
import json
import os

import guardrails as G
from audit_log import log_event

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


CUSTOMERS = _load("customers.json")
BOOKINGS = _load("bookings.json")
RULES = _load("rules.json")


def _booking(ref):
    return BOOKINGS.get(ref.upper())


def _primary_flight(ref):
    return _booking(ref)["flights"][0]


def _deny(customer, action, params, reason, rule):
    log_event(action, customer, params, f"DENIED: {reason}", rule)
    return {"status": "denied", "message": reason, "rule_cited": rule}


def _ok(customer, action, params, message, rule, escalation=False):
    log_event(action, customer, params, "APPROVED" if not escalation else "ESCALATED",
              rule, escalation)
    return {"status": "escalated" if escalation else "approved",
            "message": message, "rule_cited": rule}


# ---------------- Tool implementations ----------------

def lookup_booking(booking_ref: str):
    b = _booking(booking_ref)
    if not b:
        return {"status": "error", "message": f"No booking found for reference {booking_ref}."}
    log_event("lookup_booking", b["customer"], {"booking_ref": booking_ref}, "APPROVED", "Allowed: provide the customer's own booking and flight status information")
    return {"status": "approved", "booking": b}


def issue_meal_voucher(booking_ref: str):
    b = _booking(booking_ref)
    if not b:
        return {"status": "error", "message": "Booking not found."}
    f = _primary_flight(booking_ref)
    hours = f.get("delay_hours", 0)
    tier = G.delay_tier(hours)
    if hours == 0:
        return _deny(b["customer"], "issue_meal_voucher", {"booking_ref": booking_ref},
                     "No delay on this booking; meal voucher not applicable.",
                     "Delay Compensation Rule")
    msg = ("Meal voucher issued."
           + (" (Rs 500 per policy for delays under 3 hours.)" if tier == "tier1" else ""))
    return _ok(b["customer"], "issue_meal_voucher",
               {"booking_ref": booking_ref, "delay_hours": hours},
               msg, "Delay Compensation Rule")


def grant_lounge_access(booking_ref: str):
    b = _booking(booking_ref)
    if not b:
        return {"status": "error", "message": "Booking not found."}
    hours = _primary_flight(booking_ref).get("delay_hours", 0)
    if not G.lounge_allowed(hours):
        return _deny(b["customer"], "grant_lounge_access", {"booking_ref": booking_ref, "delay_hours": hours},
                     f"Lounge access applies only to delays of more than {G.LOUNGE_THRESHOLD_HOURS} hours. "
                     f"This delay is {hours}h.",
                     "Delay Compensation Rule")
    return _ok(b["customer"], "grant_lounge_access", {"booking_ref": booking_ref, "delay_hours": hours},
               "Lounge access granted.", "Delay Compensation Rule")


def arrange_hotel(booking_ref: str):
    b = _booking(booking_ref)
    if not b:
        return {"status": "error", "message": "Booking not found."}
    hours = _primary_flight(booking_ref).get("delay_hours", 0)
    if not G.hotel_allowed(hours):
        return _deny(b["customer"], "arrange_hotel", {"booking_ref": booking_ref, "delay_hours": hours},
                     f"Hotel accommodation applies only to delays of more than {G.HOTEL_THRESHOLD_HOURS} hours. "
                     f"This delay is {hours}h.",
                     "Delay Compensation Rule")
    return _ok(b["customer"], "arrange_hotel", {"booking_ref": booking_ref, "delay_hours": hours},
               "Hotel accommodation arranged, covering only the delayed hours "
               "(not a full night's stay).", "Delay Compensation Rule")


def rebook_flight(booking_ref: str):
    b = _booking(booking_ref)
    if not b:
        return {"status": "error", "message": "Booking not found."}
    f = _primary_flight(booking_ref)
    if "cancelled" not in f["status"].lower():
        return _deny(b["customer"], "rebook_flight", {"booking_ref": booking_ref},
                     "Free rebooking applies only to airline-caused cancellations.",
                     "Cancellation Rebooking Rule")
    priority = (" As a Gold/Platinum customer you get priority rebooking "
                "(first access to next-available seats)."
                if b["loyalty_tier"] in ("Gold", "Platinum") else "")
    msg = (f"Rebooked at no charge on the next available flight within 24 hours "
           f"(no specific flight inventory is available in this system).{priority} "
           f"Your return flight is unaffected.")
    return _ok(b["customer"], "rebook_flight", {"booking_ref": booking_ref}, msg,
               "Cancellation Rebooking Rule" + ("; Loyalty Tier Rule" if priority else ""))


def initiate_refund(booking_ref: str, payment_method: str):
    b = _booking(booking_ref)
    if not b:
        return {"status": "error", "message": "Booking not found."}
    f = _primary_flight(booking_ref)
    if "cancelled" not in f["status"].lower():
        return _deny(b["customer"], "initiate_refund", {"booking_ref": booking_ref},
                     "Refunds apply only to airline-caused cancellations.",
                     "Refund Processing Rule")
    if payment_method and payment_method.strip().lower() not in ("original", "original payment method"):
        return _deny(b["customer"], "initiate_refund",
                     {"booking_ref": booking_ref, "payment_method": payment_method},
                     "Refunds can only be issued to the original payment method.",
                     "Prohibited: processing refunds to a different payment method than the original")
    return _ok(b["customer"], "initiate_refund", {"booking_ref": booking_ref},
               f"Full refund initiated to the original payment method. It will be "
               f"processed within {G.REFUND_DAYS} business days.", "Refund Processing Rule")


def process_fare_difference(booking_ref: str, amount: float, waive_requested: bool):
    b = _booking(booking_ref)
    if not b:
        return {"status": "error", "message": "Booking not found."}
    params = {"booking_ref": booking_ref, "amount": amount, "waive_requested": waive_requested}
    if waive_requested:
        if not G.waiver_allowed(amount):
            return _deny(b["customer"], "process_fare_difference", params,
                         f"Fare differences above Rs {G.FARE_WAIVER_LIMIT} cannot be waived by an agent; "
                         f"supervisor approval is required.",
                         "Fare Difference Rule", escalation=True)
        return _ok(b["customer"], "process_fare_difference", params,
                   f"Fare difference of Rs {amount} waived (within the Rs {G.FARE_WAIVER_LIMIT} agent limit).",
                   "Fare Difference Rule")
    return _ok(b["customer"], "process_fare_difference", params,
               f"Customer will pay the fare difference of Rs {amount}.", "Fare Difference Rule")


def escalate_to_human(booking_ref: str, reason: str):
    name = _booking(booking_ref)["customer"] if _booking(booking_ref) else "Unknown"
    return _ok(name, "escalate_to_human", {"booking_ref": booking_ref, "reason": reason},
               "Escalated to a human agent/specialist team; they will reach out directly.",
               "Prohibited actions list / escalation policy", escalation=True)


# ---------------- Tool schemas (OpenAI function-calling format) ----------------

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "lookup_booking", "description": "Look up a customer's booking, flight status and loyalty tier by booking reference (PNR).", "parameters": {"type": "object", "properties": {"booking_ref": {"type": "string"}}, "required": ["booking_ref"]}}},
    {"type": "function", "function": {"name": "issue_meal_voucher", "description": "Issue a meal voucher for a delayed flight. Only valid when the flight has a delay.", "parameters": {"type": "object", "properties": {"booking_ref": {"type": "string"}}, "required": ["booking_ref"]}}},
    {"type": "function", "function": {"name": "grant_lounge_access", "description": "Grant lounge access. Policy: only for delays of more than 3 hours. Guardrail enforces this.", "parameters": {"type": "object", "properties": {"booking_ref": {"type": "string"}}, "required": ["booking_ref"]}}},
    {"type": "function", "function": {"name": "arrange_hotel", "description": "Arrange hotel accommodation covering ONLY the delayed hours (never a full night). Policy: only for delays of more than 5 hours. Guardrail enforces this.", "parameters": {"type": "object", "properties": {"booking_ref": {"type": "string"}}, "required": ["booking_ref"]}}},
    {"type": "function", "function": {"name": "rebook_flight", "description": "Free rebooking on the next available flight within 24 hours. Policy: only for airline-caused cancellations. Guardrail enforces this.", "parameters": {"type": "object", "properties": {"booking_ref": {"type": "string"}}, "required": ["booking_ref"]}}},
    {"type": "function", "function": {"name": "initiate_refund", "description": "Initiate a full refund for an airline-caused cancellation. Refunds go to the ORIGINAL payment method only, within 7 business days. Guardrail enforces both.", "parameters": {"type": "object", "properties": {"booking_ref": {"type": "string"}, "payment_method": {"type": "string", "description": "'original' for the original payment method, or the method the customer requests"}}, "required": ["booking_ref", "payment_method"]}}},
    {"type": "function", "function": {"name": "process_fare_difference", "description": "Handle a voluntary move to a higher-fare flight. Customer pays the difference; agent may waive only up to Rs 1,500 (above that, use with waive_requested=true and it will escalate).", "parameters": {"type": "object", "properties": {"booking_ref": {"type": "string"}, "amount": {"type": "number"}, "waive_requested": {"type": "boolean", "description": "true if the customer asks the agent to waive the fare difference"}}, "required": ["booking_ref", "amount", "waive_requested"]}}},
    {"type": "function", "function": {"name": "escalate_to_human", "description": "Escalate to a human agent. REQUIRED for: compensation beyond stated policy, fare-difference waivers above Rs 1,500, threats of legal action or formal complaints, refunds to a different payment method, or any request the agent lacks authority for.", "parameters": {"type": "object", "properties": {"booking_ref": {"type": "string"}, "reason": {"type": "string"}}, "required": ["booking_ref", "reason"]}}},
]

_DISPATCH = {
    "lookup_booking": lambda a: lookup_booking(a["booking_ref"]),
    "issue_meal_voucher": lambda a: issue_meal_voucher(a["booking_ref"]),
    "grant_lounge_access": lambda a: grant_lounge_access(a["booking_ref"]),
    "arrange_hotel": lambda a: arrange_hotel(a["booking_ref"]),
    "rebook_flight": lambda a: rebook_flight(a["booking_ref"]),
    "initiate_refund": lambda a: initiate_refund(a["booking_ref"], a["payment_method"]),
    "process_fare_difference": lambda a: process_fare_difference(a["booking_ref"], a["amount"], a["waive_requested"]),
    "escalate_to_human": lambda a: escalate_to_human(a["booking_ref"], a["reason"]),
}


def execute_tool(name: str, args: dict) -> dict:
    try:
        return _DISPATCH[name](args)
    except Exception as e:
        return {"status": "error", "message": f"Tool error: {e}"}
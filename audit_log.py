"""Append-only audit trail: every tool call is recorded with the rule cited."""
import json
import os
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "audit_log.jsonl")


def log_event(action: str, customer: str, params: dict, outcome: str,
              rule_cited: str, escalation: bool = False) -> dict:
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "customer": customer,
        "action": action,
        "params": params,
        "outcome": outcome,
        "rule_cited": rule_cited,
        "escalation": escalation,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def read_log(last_n: int = 30) -> list:
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, encoding="utf-8") as f:
        lines = f.readlines()
    return [json.loads(l) for l in lines[-last_n:]]
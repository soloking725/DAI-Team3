"""
In-account reminders — no email/SMS, since there's no SMTP configured yet.
Everything here only ever renders as an in-app banner (see
pages/04_Ask_a_Question.py and pages/05_Post_Visa_Guide.py), computed fresh
on every page load. Nothing is scheduled or sent anywhere.

Two sources feed the same banner:
- compute_reminders(): built-in, derived from dates the student entered
  themselves (shared/vera_state.py's "post_visa" block) — visa/passport
  expiration.
- compute_custom_reminders(): arbitrary reminders a DSO authored for their
  whole college (shared/db.py's custom_reminders table) — e.g. "report your
  enrolled courses by Sept 5", an OPT unemployment-limit check-in, a program
  extension deadline. Same urgency/threshold logic, DSO-supplied title/detail.
"""

import datetime

# (days-until-expiration threshold, urgency label) — first matching threshold wins.
_THRESHOLDS = [
    (30, "urgent"),
    (90, "warning"),
    (180, "notice"),
]


def _parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _urgency_for(days_left: int) -> str | None:
    if days_left < 0:
        return "urgent"
    for threshold, urgency in _THRESHOLDS:
        if days_left <= threshold:
            return urgency
    return None


def _reminder_for(label: str, iso_date: str, today: datetime.date) -> dict | None:
    date = _parse_date(iso_date)
    if date is None:
        return None
    days_left = (date - today).days
    urgency = _urgency_for(days_left)
    if urgency is None:
        return None
    if days_left < 0:
        return {
            "title": f"{label} has expired",
            "detail": f"Your {label.lower()} expired on {date.isoformat()}. Renew it as soon as possible.",
            "urgency": "urgent",
            "days_left": days_left,
        }
    return {
        "title": f"{label} expiring soon",
        "detail": f"Your {label.lower()} expires on {date.isoformat()} — {days_left} day(s) from now.",
        "urgency": urgency,
        "days_left": days_left,
    }


def compute_reminders(post_visa: dict) -> list:
    """Returns a list of reminder dicts ({title, detail, urgency, days_left}),
    most urgent first. Empty if no dates are set or nothing is within any
    threshold yet."""
    post_visa = post_visa or {}
    today = datetime.date.today()
    reminders = [
        r for r in (
            _reminder_for("Visa", post_visa.get("visa_expiration", ""), today),
            _reminder_for("Passport", post_visa.get("passport_expiration", ""), today),
        )
        if r is not None
    ]
    reminders.sort(key=lambda r: r["days_left"])
    return reminders


def compute_custom_reminders(custom_reminders: list) -> list:
    """custom_reminders: rows from shared/db.py's list_custom_reminders()
    (each with title, detail, due_date). Returns the same reminder-dict shape
    as compute_reminders(), using the DSO's own title/detail verbatim plus a
    computed due-date note, filtered/sorted by the same urgency thresholds."""
    today = datetime.date.today()
    reminders = []
    for r in custom_reminders or []:
        due = _parse_date(r.get("due_date", ""))
        if due is None:
            continue
        days_left = (due - today).days
        urgency = _urgency_for(days_left)
        if urgency is None:
            continue
        when = f"(was due {due.isoformat()})" if days_left < 0 else f"(due {due.isoformat()} — {days_left} day(s) from now)"
        reminders.append({
            "title": r["title"],
            "detail": f"{r['detail']} {when}",
            "urgency": urgency,
            "days_left": days_left,
        })
    reminders.sort(key=lambda r: r["days_left"])
    return reminders

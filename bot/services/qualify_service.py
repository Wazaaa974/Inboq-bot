"""Lead qualification — deterministic rule-based scoring. No OpenAI calls."""

import re
from typing import Any

# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------

_GROSS_WORDS = [
    "pute", "salope", "connasse", "bitch", "conne", "chienne", "merde",
    "enculé", "enculee", "fdp", "ta gueule", "ferme ta gueule",
]

_NEGOTIATION_PATTERNS = [
    r"\bmoins cher\b",
    r"\br[ée]duction\b",
    r"\bprix sp[ée]cial\b",
    r"\btu fais un geste\b",
    r"\bfais un effort\b",
    r"\bc'est trop cher\b",
    r"\bc est trop cher\b",
    r"\bnégocier?\b",
    r"\bnegocie?r?\b",
    r"\bdiscuter le prix\b",
    r"\bpromo\b",
    r"\bremise\b",
    r"\btarif pr[ée]f[ée]rentiel\b",
]

# Patterns that signal a date/time was mentioned
_DATE_PATTERNS = [
    r"\b(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b",
    r"\b(demain|après-demain|apres-demain|ce soir|cet après-midi|ce matin|cette semaine|ce week-end)\b",
    r"\b\d{1,2}[/\-.]\d{1,2}([/\-.]\d{2,4})?\b",   # dd/mm or dd/mm/yyyy
    r"\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b",
    r"\b(matin|après-midi|soir|nuit|midi|soirée)\b",
    r"\b\d{1,2}h\d{0,2}\b",                          # 14h or 14h30
    r"\b(prochain(e)?|cette|en fin de semaine)\b",
]

# Patterns that indicate a "too vague" message (exact match on full message)
_VAGUE_EXACT = {"dispo ?", "dispo?", "t'es là ?", "t'es la ?", "cc", "allo", "allô", "tu es là ?", "tu es la ?", "bonjour"}


def _normalize(text: str) -> str:
    return text.lower().strip()


def _contains_gross_word(text: str) -> bool:
    t = _normalize(text)
    return any(word in t for word in _GROSS_WORDS)


def _contains_negotiation(text: str) -> bool:
    t = _normalize(text)
    return any(re.search(p, t) for p in _NEGOTIATION_PATTERNS)


def _contains_date(text: str) -> bool:
    t = _normalize(text)
    return any(re.search(p, t) for p in _DATE_PATTERNS)


def _is_too_vague(text: str) -> bool:
    t = _normalize(text)
    if t in _VAGUE_EXACT:
        return True
    if len(text.strip()) < 15:
        return True
    return False


def _has_excessive_caps(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 10:
        return False
    return sum(1 for c in letters if c.isupper()) / len(letters) > 0.6


def _service_identified(text: str, history: list[dict], config: dict) -> bool:
    """Check if any configured service name appears in the message or history."""
    services = [s["name"].lower() for s in config.get("services", [])]
    all_text = _normalize(text) + " " + " ".join(
        _normalize(m.get("content", "")) for m in history
    )
    return any(svc in all_text for svc in services)


def _date_in_conversation(text: str, history: list[dict]) -> bool:
    all_text = text + " " + " ".join(m.get("content", "") for m in history)
    return _contains_date(all_text)


def _is_developed_message(text: str) -> bool:
    """More than 40 chars AND not just a closed yes/no question."""
    if len(text.strip()) <= 40:
        return False
    # Closed one-liner questions (short and ends with ?)
    if text.strip().endswith("?") and len(text.strip()) < 60:
        words = text.strip().split()
        if len(words) <= 6:
            return False
    return True


def _next_qualifying_question(history: list[dict], questions: list[str]) -> str | None:
    """Return first question whose topic hasn't been addressed in history yet."""
    history_text = " ".join(_normalize(m.get("content", "")) for m in history)

    # Simple heuristics to detect if each question was already answered
    question_answered_hints = [
        # "Quelle prestation" → any service keyword or detailed description
        lambda h: any(kw in h for kw in ["prestation", "coupe", "coloration", "soin", "balayage", "kératine", "mariée", "massage", "rendez-vous", "rdv"]),
        # "date ou créneau" → date/time detected in history
        lambda h: _contains_date(h),
        # "première fois" → any indicator
        lambda h: any(kw in h for kw in ["première fois", "premiere fois", "jamais", "déjà", "deja", "oui", "non", "habituée", "habituee", "nouvelle"]),
    ]

    for question, is_answered in zip(questions, question_answered_hints):
        if not is_answered(history_text):
            return question
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_message(
    message_text: str,
    history: list[dict],
    config: dict,
) -> dict[str, Any]:
    """
    Score a message deterministically based on client config rules.

    Returns:
        {
            "score": int,             # 0-5
            "reasons": list[str],
            "disqualified": bool,
            "disqualify_reason": str,
            "should_ask": str | None,
        }
    """
    qual_config = config.get("qualification", {})
    criteria_weights = qual_config.get("criteria", {})
    qualifying_questions = qual_config.get("qualifying_questions", [])

    # ------------------------------------------------------------------
    # 1. Disqualification checks (short-circuit)
    # ------------------------------------------------------------------
    if _contains_gross_word(message_text):
        return _disqualified("irrespectueux")

    if _is_too_vague(message_text):
        return _disqualified("trop vague")

    if _contains_negotiation(message_text):
        return _disqualified("négociation de tarif")

    # ------------------------------------------------------------------
    # 2. Scoring
    # ------------------------------------------------------------------
    score = 0
    reasons = []

    # ton_respectueux
    if not _has_excessive_caps(message_text) and not _contains_gross_word(message_text):
        score += criteria_weights.get("ton_respectueux", 1)
        reasons.append("ton respectueux")

    # prestation_identifiee
    if _service_identified(message_text, history, config):
        score += criteria_weights.get("prestation_identifiee", 1)
        reasons.append("prestation identifiée")

    # date_mentionnee
    if _date_in_conversation(message_text, history):
        score += criteria_weights.get("date_mentionnee", 1)
        reasons.append("date mentionnée")

    # tarif_accepte
    if not _contains_negotiation(message_text):
        score += criteria_weights.get("tarif_accepte", 1)
        reasons.append("tarif accepté")

    # message_developpe
    if _is_developed_message(message_text):
        score += criteria_weights.get("message_developpe", 1)
        reasons.append("message développé")

    # ------------------------------------------------------------------
    # 3. Next qualifying question
    # ------------------------------------------------------------------
    should_ask = _next_qualifying_question(history + [{"role": "user", "content": message_text}], qualifying_questions)

    return {
        "score": score,
        "reasons": reasons,
        "disqualified": False,
        "disqualify_reason": "",
        "should_ask": should_ask,
    }


def _disqualified(reason: str) -> dict[str, Any]:
    return {
        "score": 0,
        "reasons": [],
        "disqualified": True,
        "disqualify_reason": reason,
        "should_ask": None,
    }

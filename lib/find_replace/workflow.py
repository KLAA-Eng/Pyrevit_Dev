# -*- coding: utf-8 -*-
"""Host-independent name planning and result formatting."""


def rename_value(current, find_text, replace_text, prefix, suffix):
    """Return the exact requested value; never invent a collision suffix."""
    if replace_text and not find_text:
        raise ValueError("Enter Find text before using Replace.")
    middle = current.replace(find_text, replace_text) if find_text else current
    return prefix + middle + suffix


def case_value(current, mode):
    if mode == "upper":
        return current.upper()
    if mode == "lower":
        return current.lower()
    raise ValueError("Unsupported case conversion.")


def new_result(action):
    return {"action": action, "changed": [], "unchanged": [],
            "skipped": [], "failed": [], "error": None}


def record(result, kind, label, reason=None):
    result[kind].append((label, reason))


def unresolved(result):
    return bool(result["skipped"] or result["failed"] or result["error"])


def summary(result):
    return ("{0}: {1} changed, {2} unchanged, {3} skipped, {4} failed".format(
        result["action"], len(result["changed"]), len(result["unchanged"]),
        len(result["skipped"]), len(result["failed"])))


def details(result):
    lines = []
    if result["error"]:
        lines.append(result["error"])
    for kind in ("skipped", "failed"):
        for label, reason in result[kind]:
            lines.append("{0}: {1} - {2}".format(kind.capitalize(), label,
                                                reason or "No reason supplied"))
    return "\n".join(lines)

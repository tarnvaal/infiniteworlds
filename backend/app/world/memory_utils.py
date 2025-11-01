from typing import List


def sanitize_entities(entities) -> List[str]:
    """Drop generic entities and dedupe case-insensitively."""
    if not entities:
        return []
    blacklist = {"player"}
    seen_lower = set()
    cleaned: List[str] = []
    for e in entities:
        if not isinstance(e, str):
            continue
        el = e.strip()
        if not el:
            continue
        if el.lower() in blacklist:
            continue
        key = el.lower()
        if key in seen_lower:
            continue
        seen_lower.add(key)
        cleaned.append(el)
    return cleaned

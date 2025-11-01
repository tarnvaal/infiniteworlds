import time
from typing import List, Dict, Any, Tuple

from ..utility.embeddings import dot_sim
from .memory import WorldMemory


def _type_bonus(mem_type: str) -> float:
    t = (mem_type or "").lower()
    if t == "threat":
        return 0.06
    if t in ("npc", "relationship"):
        return 0.05
    if t == "goal":
        return 0.04
    if t == "item":
        return 0.02
    return 0.0


def weighted_retrieve(
    world_memory: WorldMemory, query: str, k: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve memories with simple weighting (similarity + recency + type bonus).

    Returns: top-k memory dicts sorted by weighted score.
    """
    base = world_memory.retrieve(query, k=max(k * 2, 5))
    if not base:
        return []

    now = time.time()
    qvec = world_memory.embed_fn(query)

    weighted: List[Tuple[float, float, float, float, Dict[str, Any]]] = []
    for m in base:
        score = dot_sim(qvec, m["vector"])  # similarity
        age_sec = max(0.0, now - float(m.get("timestamp", now)))
        recency = pow(0.5, age_sec / 600.0) * 0.05  # half-life ~10 min, max +0.05
        bonus = _type_bonus(str(m.get("type", "")))
        total = score + recency + bonus
        weighted.append((total, score, recency, bonus, m))

    weighted.sort(key=lambda x: x[0], reverse=True)
    top = weighted[:k]
    return [m for (_, _, _, _, m) in top]


def format_world_facts(
    memories: List[Dict[str, Any]] | None, char_cap: int = 800
) -> str:
    """Format a compact world facts string for prompt injection."""
    if not memories:
        return ""
    lines: List[str] = ["World Facts (use to stay consistent; do not contradict):"]
    for m in memories:
        ents = ", ".join(map(str, m.get("entities", [])))
        line = f"- [{m.get('type','unknown')}] {m.get('summary','').strip()}"
        if ents:
            line += f" (entities: {ents})"
        lines.append(line)

    out = "\n".join(lines)
    if len(out) > char_cap:
        keep = [lines[0]]
        for line in lines[1:]:
            if len("\n".join(keep + [line])) > char_cap:
                break
            keep.append(line)
        out = "\n".join(keep)
    return out


def format_npc_cards(
    npc_snaps: List[Dict[str, Any]] | None, max_cards: int = 2, char_cap: int = 350
) -> str:
    if not npc_snaps:
        return ""
    cards: List[str] = ["NPC Cards:"]
    for snap in npc_snaps[:max_cards]:
        name = snap.get("name", "Unknown")
        rel = snap.get("relationship_to_player", "unknown")
        loc = snap.get("last_seen_location") or "unknown"
        intent = snap.get("intent") or "unknown"
        line = f"- {name}: rel={rel}; last_seen={loc}; intent={intent}"
        cards.append(line[:char_cap])
    return "\n".join(cards)

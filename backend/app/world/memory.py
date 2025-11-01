import time
import uuid
from typing import List, Dict, Any, Tuple

from ..utility.embeddings import dot_sim


class WorldMemory:
    def __init__(self, embed_fn):
        self.memories: List[Dict[str, Any]] = []
        self.embed_fn = embed_fn
        # Lightweight NPC index mapping canonical_name -> snapshot dict
        self.npc_index: Dict[str, Dict[str, Any]] = {}

    def add_memory(
        self,
        summary: str,
        entities: List[str],
        mem_type: str,
        npc: Dict[str, Any] | None = None,
        dedupe_check: bool = False,
        similarity_threshold: float = 0.85,
    ) -> str:
        """Store a durable world fact."""
        if dedupe_check and self.memories:
            vec = self.embed_fn(summary)
            recent_memories = self.memories[-10:]
            for memory in recent_memories:
                similarity = dot_sim(vec, memory["vector"])
                if similarity >= similarity_threshold:
                    return memory["id"]

        memory_id = str(uuid.uuid4())
        vec = self.embed_fn(summary)

        entry = {
            "id": memory_id,
            "summary": summary,
            "entities": entities,
            "type": mem_type,
            "timestamp": time.time(),
            "vector": vec,
        }

        self.memories.append(entry)
        # If this is an NPC memory with structured data, upsert the NPC snapshot
        npc_payload = npc
        if mem_type == "npc" and isinstance(npc_payload, dict):
            self._upsert_npc_from_payload(npc_payload, entry)
        return memory_id

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Return top-k relevant memories by cosine similarity.
        """
        qvec = self.embed_fn(query)

        # qvec and m["vector"] are both normalized  dot product
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for m in self.memories:
            score = dot_sim(qvec, m["vector"])
            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for (score, m) in scored[:k]]

    # ---------- NPC support ----------
    def _canonicalize_name(self, name: str) -> str:
        return " ".join(name.strip().lower().split())

    def _upsert_npc_from_payload(
        self, npc: Dict[str, Any], source_entry: Dict[str, Any]
    ):
        name = str(npc.get("name", "")).strip()
        if not name:
            return
        cid = self._canonicalize_name(name)

        now = time.time()
        snapshot = self.npc_index.get(
            cid,
            {
                "name": name,
                "aliases": [],
                "last_seen_location": None,
                "last_seen_time": 0.0,
                "intent": None,
                "relationship_to_player": "unknown",
                "history": [],
                "confidence": 0.0,
            },
        )

        # merge aliases
        aliases = npc.get("aliases", []) or []
        if isinstance(aliases, list):
            existing = {
                self._canonicalize_name(a): a for a in snapshot.get("aliases", [])
            }
            for a in aliases:
                if isinstance(a, str):
                    key = self._canonicalize_name(a)
                    if key not in existing and key != cid:
                        snapshot["aliases"].append(a)

        # update last seen
        loc = npc.get("last_seen_location")
        if isinstance(loc, str) and loc.strip():
            snapshot["last_seen_location"] = loc.strip()
            snapshot["last_seen_time"] = now

        # update intent (replace if provided and non-empty)
        intent = npc.get("intent")
        if isinstance(intent, str) and intent.strip():
            snapshot["intent"] = intent.strip()

        # relationship precedence: hostile > friendly > neutral > unknown
        rel = str(npc.get("relationship_to_player", "")).lower().strip()
        order = {"hostile": 3, "friendly": 2, "neutral": 1, "unknown": 0}
        if rel in order:
            current = str(snapshot.get("relationship_to_player", "unknown")).lower()
            if order.get(rel, 0) >= order.get(current, 0):
                snapshot["relationship_to_player"] = rel

        # confidence (max)
        conf = npc.get("confidence")
        try:
            cval = float(conf)
            snapshot["confidence"] = max(float(snapshot.get("confidence", 0.0)), cval)
        except Exception:
            pass

        # append concise history line
        history_line = source_entry.get("summary")
        if isinstance(history_line, str) and history_line:
            hist = snapshot.get("history", [])
            hist.append(history_line[:160])
            snapshot["history"] = hist[-10:]  # cap length

        self.npc_index[cid] = snapshot

    def get_relevant_npc_snapshots(
        self, query: str, k: int = 2
    ) -> List[Dict[str, Any]]:
        """Return up to k NPC snapshots relevant to the query by name/alias similarity."""
        if not self.npc_index:
            return []
        qvec = self.embed_fn(query)

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for snap in self.npc_index.values():
            # build a small text rep for similarity: name + aliases + intent + location
            parts = [snap.get("name", "")]
            parts.extend(snap.get("aliases", []) or [])
            parts.append(snap.get("intent", "") or "")
            parts.append(snap.get("last_seen_location", "") or "")
            text = " | ".join([p for p in parts if p])
            svec = self.embed_fn(text) if text else qvec
            score = dot_sim(qvec, svec)
            # slight boost for recency
            age_sec = max(0.0, time.time() - float(snap.get("last_seen_time", 0.0)))
            recency = pow(0.5, age_sec / 600.0) * 0.05
            scored.append((score + recency, snap))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [snap for (_, snap) in scored[:k]]

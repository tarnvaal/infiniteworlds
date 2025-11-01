#!/usr/bin/env python3
"""
Console debug interface for PersistentDM.
Allows interactive chat with the DM while showing embeddings, vectors, and world memory.
"""

import signal
import sys
import time

from app.utility.llama import Chatter
from app.world.memory import WorldMemory
from app.utility.embeddings import get_embedding_model, dot_sim


def signal_handler(signum, frame):
    """Handle termination signals to ensure clean shutdown."""
    print(f"\nReceived signal {signum}. Exiting...")
    sys.exit(0)


class DebugConsole:
    def __init__(self, model_path: str = "~/dev/llm/Harbinger-24B-Q5_K_M.gguf"):
        print("Initializing Debug Console...")

        # Initialize components
        self.chatter = Chatter(model_path)
        self.embed_model = get_embedding_model()
        self.world_memory = WorldMemory(self.embed_model.embed)

        # Chat history for context
        self.chat_history = []

        print("✓ Components initialized successfully")

    def show_embedding(self, text: str, label: str = "Text", show_text: bool = True):
        """Display text and its embedding vector."""
        print(f"\n--- {label} Embedding ---")
        if show_text:
            print(f"Text: {text}")

        vector = self.embed_model.embed(text)
        print(f"Vector (first 10 dims): {vector[:10]}...")
        print(f"Vector magnitude: {sum(x*x for x in vector)**0.5:.4f}")
        print(f"Vector length: {len(vector)}")

        return vector

    def show_memory_state(self):
        """Display current world memory contents."""
        print("\n--- World Memory State ---")
        if not self.world_memory.memories:
            print("No memories stored yet.")
            return

        for i, memory in enumerate(self.world_memory.memories, 1):
            print(f"\n{i}. {memory['summary']}")
            print(f"   Type: {memory['type']}")
            print(f"   Entities: {memory['entities']}")
            print(
                f"   Timestamp: {time.strftime('%H:%M:%S', time.localtime(memory['timestamp']))}"
            )
            print(f"   Vector dims: {len(memory['vector'])}")

    def find_similar_memories(self, query: str, k: int = 3):
        """Find and display similar memories."""
        print(f"\n--- Similar Memories for: '{query}' ---")

        query_vec = self.embed_model.embed(query)
        similar = self.world_memory.retrieve(query, k=k)

        if not similar:
            print("No similar memories found.")
            return

        for i, memory in enumerate(similar, 1):
            score = dot_sim(query_vec, memory["vector"])
            print(f"\n{i}. Similarity: {score:.4f}")
            print(f"   Summary: {memory['summary']}")
            print(f"   Type: {memory['type']}")
            print(f"   Entities: {memory['entities']}")

    def _weighted_retrieve(self, query: str, k: int = 5):
        """Retrieve memories with simple weighting (similarity + recency + type bonus)."""
        # base top-k by cosine
        base = self.world_memory.retrieve(query, k=max(k * 2, 5))

        if not base:
            return []

        now = time.time()

        def type_bonus(mem_type: str) -> float:
            t = (mem_type or "").lower()
            if t == "threat":
                return 0.06
            if t in ("npc", "relationship"):
                return 0.05
            if t == "goal":
                return 0.04
            if t == "item":
                return 0.02
            # locations/world_state/other -> 0.0
            return 0.0

        weighted = []
        qvec = self.embed_model.embed(query)
        for m in base:
            # similarity (recompute to show in logs reliably)
            score = dot_sim(qvec, m["vector"])  # type: ignore
            # recency boost: half-life ~10 minutes
            age_sec = max(0.0, now - float(m.get("timestamp", now)))
            recency = pow(0.5, age_sec / 600.0) * 0.05  # max +0.05 right after creation
            bonus = type_bonus(str(m.get("type", "")))
            total = score + recency + bonus
            weighted.append((total, score, recency, bonus, m))

        weighted.sort(key=lambda x: x[0], reverse=True)
        top = weighted[:k]

        # Log details
        print(f"\n--- Similar Memories for: '{query}' (weighted) ---")
        for i, (total, score, recency, bonus, m) in enumerate(top, 1):
            print(
                f"\n{i}. Total: {total:.4f} | sim: {score:.4f} | rec: {recency:.3f} | bonus: {bonus:.3f}"
            )
            print(f"   Summary: {m['summary']}")
            print(f"   Type: {m['type']}")
            print(f"   Entities: {m['entities']}")

        return [m for (_, _, _, _, m) in top]

    def _format_world_facts(self, memories, char_cap: int = 800) -> str:
        """Format a compact world facts string for prompt injection."""
        if not memories:
            return ""
        lines = ["World Facts (use to stay consistent; do not contradict):"]
        for m in memories:
            ents = ", ".join(map(str, m.get("entities", [])))
            line = f"- [{m.get('type','unknown')}] {m.get('summary','').strip()}"
            if ents:
                line += f" (entities: {ents})"
            lines.append(line)

        out = "\n".join(lines)
        if len(out) > char_cap:
            # trim roughly by dropping tail lines
            keep = [lines[0]]
            for line in lines[1:]:
                if len("\n".join(keep + [line])) > char_cap:
                    break
                keep.append(line)
            out = "\n".join(keep)
        return out

    def _sanitize_entities(self, entities):
        """Drop generic entities and dedupe case-insensitively."""
        if not entities:
            return []
        blacklist = {"player"}
        seen_lower = set()
        cleaned = []
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

    def _format_npc_cards(
        self, npc_snaps, max_cards: int = 2, char_cap: int = 350
    ) -> str:
        if not npc_snaps:
            return ""
        cards = ["NPC Cards:"]
        for snap in npc_snaps[:max_cards]:
            name = snap.get("name", "Unknown")
            rel = snap.get("relationship_to_player", "unknown")
            loc = snap.get("last_seen_location") or "unknown"
            intent = snap.get("intent") or "unknown"
            line = f"- {name}: rel={rel}; last_seen={loc}; intent={intent}"
            cards.append(line[:char_cap])
        return "\n".join(cards)

    def add_sample_memories(self):
        """Add some sample memories for testing."""
        print("\nAdding sample memories...")

        samples = [
            (
                "The player discovers an ancient tome in the library",
                ["player", "tome", "library"],
                "item_change",
            ),
            (
                "Guard patrol increased after the theft",
                ["guard", "patrol", "theft"],
                "security_change",
            ),
            (
                "Merchant offers information about the black market",
                ["merchant", "information", "black_market"],
                "relationship_change",
            ),
            (
                "Hidden passage discovered behind bookshelf",
                ["passage", "bookshelf"],
                "location_change",
            ),
        ]

        for summary, entities, mem_type in samples:
            mem_id = self.world_memory.add_memory(summary, entities, mem_type)
            print(f"✓ Added: {summary[:50]}... (ID: {mem_id[:8]})")

    def process_chat_message(self, user_message: str):
        """Process a chat message and show all the internal processing."""
        print(f"\n{'='*60}")
        print(f"USER: {user_message}")
        print(f"{'='*60}")

        # Show user message embedding
        user_vec = self.show_embedding(user_message, "User Message")

        # Find similar memories
        self.find_similar_memories(user_message)

        # Retrieve and inject world facts into the DM prompt
        weighted = self._weighted_retrieve(user_message, k=4)
        facts_str = self._format_world_facts(weighted)
        if facts_str:
            print(f"\n--- Injecting World Facts ---\n{facts_str}")
        # Also inject NPC cards from core engine
        npc_snaps = self.world_memory.get_relevant_npc_snapshots(user_message, k=2)
        npc_cards = self._format_npc_cards(npc_snaps)
        if npc_cards:
            print(f"\n--- Injecting NPC Cards ---\n{npc_cards}")

        # Get DM response
        print("\n--- DM Response Generation ---")
        start_time = time.time()
        # Merge NPC cards before world facts for model guidance
        merged_context = None
        if npc_cards and facts_str:
            merged_context = npc_cards + "\n\n" + facts_str
        elif npc_cards:
            merged_context = npc_cards
        else:
            merged_context = facts_str if facts_str else None

        dm_response = self.chatter.chat(user_message, world_facts=merged_context)
        response_time = time.time() - start_time
        print(f"Response time: {response_time:.2f}s")
        print(f"DM: {dm_response}")

        # Show DM response embedding
        dm_vec = self.show_embedding(dm_response, "DM Response", show_text=False)

        # Show similarity between user and DM
        similarity = dot_sim(user_vec, dm_vec)
        print(f"\nUser-DM similarity: {similarity:.4f}")

        # Record history
        self.chat_history.append({"role": "user", "text": user_message})
        self.chat_history.append({"role": "dm", "text": dm_response})

        # Try to extract memorable facts from the conversation
        print("\n--- Memory Analysis ---")
        start_time = time.time()

        # Create a simple summary of the conversation turn
        conversation_context = {
            "user_message": user_message,
            "dm_response": dm_response,
            "context": f"Player said: {user_message}\n\nDM responded: {dm_response}",
        }

        summary = self.chatter.analyze_conversation_for_memories(conversation_context)
        analysis_time = time.time() - start_time
        print(f"Analysis time: {analysis_time:.2f}s")

        if summary:
            print("\n📝 Potential Memory Detected:")
            print(f"  Summary: {summary['summary']}")
            print(f"  Type: {summary['type']}")
            print(f"  Entities: {summary['entities']}")
            conf = float(summary.get("confidence", 0.8))
            print(f"  Confidence: {conf:.2f}")

            # Add to world memory if significant
            if conf > 0.6:  # Lower threshold to see more memory creation
                entities = self._sanitize_entities(summary["entities"])
                npc_payload = summary.get("npc") if isinstance(summary, dict) else None
                mem_id = self.world_memory.add_memory(
                    summary["summary"], entities, summary["type"], npc=npc_payload
                )
                print(f"\n  ✅ MEMORY STORED (ID: {mem_id[:8]})")
            else:
                print(f"\n  ❌ REJECTED - Confidence too low ({conf:.2f} < 0.6)")
        else:
            print("❌ No memorable facts detected in this exchange")

        # Show memory state
        self.show_memory_state()

    def run_interactive(self):
        """Run the interactive console."""
        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        print("\n" + "=" * 60)
        print("PersistentDM Debug Console")
        print("=" * 60)
        print("Commands:")
        print("  /memory - Show current world memory")
        print("  /embed <text> - Show embedding for text")
        print("  /similar <text> - Find similar memories")
        print("  /add_sample - Add sample memories")
        print("  /clear_memory - Clear world memory")
        print("  /quit - Exit")
        print("  Or just type a message to chat with the DM")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                if user_input == "/quit":
                    break
                elif user_input == "/memory":
                    self.show_memory_state()
                elif user_input == "/add_sample":
                    self.add_sample_memories()
                elif user_input == "/clear_memory":
                    self.world_memory.memories.clear()
                    print("✓ World memory cleared")
                elif user_input.startswith("/embed "):
                    text = user_input[7:].strip()
                    if text:
                        self.show_embedding(text)
                    else:
                        print("Usage: /embed <text>")
                elif user_input.startswith("/similar "):
                    text = user_input[9:].strip()
                    if text:
                        self.find_similar_memories(text)
                    else:
                        print("Usage: /similar <text>")
                else:
                    # Regular chat message
                    self.process_chat_message(user_input)

            except KeyboardInterrupt:
                print("\nExiting...")
                sys.exit(0)
            except Exception as e:
                print(f"Error: {e}")


def main():
    import sys
    import os

    # Set model path from environment or default
    model_path = os.getenv("MODEL_PATH", "~/dev/llm/Harbinger-24B-Q5_K_M.gguf")

    try:
        console = DebugConsole(model_path)
        console.run_interactive()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

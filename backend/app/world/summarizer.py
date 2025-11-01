from ..utility.llama import Chatter


class WorldChangeSummarizer:
    """LLM-based summarizer for detecting world changes from planner responses."""

    def __init__(self, chatter: Chatter):
        self.chatter = chatter

    def summarize_world_change(
        self, planner_json: dict, resolved_outcome: dict | None = None
    ) -> dict | None:
        """Return world change summary or None if no changes."""
        result = self.chatter.summarize_world_changes(planner_json, resolved_outcome)
        if result:
            return {
                "summary": result["summary"],
                "entities": result["entities"],
                "type": result["type"],
                "confidence": result.get("confidence", 0.8),
            }
        return None

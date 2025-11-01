def build_query(player_action: str, recent_scene: list[dict[str, str]]) -> str:
    """
    Produce a retrieval query for memory search.
    Keep it short and factual.
    """
    last_dm = ""
    for msg in reversed(recent_scene):
        if msg["role"] == "dm":
            last_dm = msg["text"]
            break

    last_user = ""
    for msg in reversed(recent_scene):
        if msg["role"] == "user":
            last_user = msg["text"]
            break

    parts = [
        "current scene:",
        last_dm,
        "latest player intent:",
        last_user,
        "new action:",
        player_action,
    ]

    return " ".join(parts)


def make_planner_prompt(
    world_facts: list[dict], recent_scene: list[dict], player_action: str
) -> list[dict]:
    """
    Returns a chat list you can hand directly to llama-cpp create_chat_completion.
    world_facts: output of wm.retrieve()
    recent_scene: [{"role": "user"/"dm", "text": "..."}]
    """

    world_context_lines = []
    for i, fact in enumerate(world_facts, start=1):
        world_context_lines.append(f"{i}. {fact['summary']}")

    scene_snippets = []
    # only last ~10 turns
    for msg in recent_scene[-20:]:
        role = "PLAYER" if msg["role"] == "user" else "DM"
        scene_snippets.append(f"{role}: {msg['text']}")

    system_block = (
        "You are the GAME PLANNER.\n"
        "Your job is to describe immediate consequences and future fallout.\n"
        "Speak in neutral third person. Do not write dialogue.\n"
        "Output strict JSON with keys:\n"
        "  narrative_setup\n"
        "  consequences_now\n"
        "  consequences_future\n"
        "  rolls_needed (list of {type, target_dc, on_success, on_fail})\n"
        "\n"
        "Return ONLY the JSON object. No commentary."
    )

    user_block = (
        "World Context:\n"
        + ("\n".join(world_context_lines) if world_context_lines else "None.")
        + "\n\nRecent Scene:\n"
        + ("\n".join(scene_snippets) if scene_snippets else "None.")
        + "\n\nPlayer Action:\n"
        + player_action
        + "\n\nAnalyze this situation and return the JSON response."
    )

    return [
        {"role": "system", "content": system_block},
        {"role": "user", "content": user_block},
    ]

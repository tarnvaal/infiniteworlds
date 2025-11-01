import os
from functools import lru_cache

from .utility.llama import Chatter


DEFAULT_MODEL_PATH = "~/dev/llm/Harbinger-24B-Q5_K_M.gguf"


@lru_cache(maxsize=1)
def get_chatter() -> Chatter:
    model_path = os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH)
    return Chatter(model_path)


def reset_chatter() -> Chatter:
    get_chatter.cache_clear()
    return get_chatter()

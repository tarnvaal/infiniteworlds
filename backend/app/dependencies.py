import os
from functools import lru_cache

from .utility.llama import chatter as LlamaChatter


DEFAULT_MODEL_PATH = "~/dev/llm/Harbinger-24B-Q5_K_M.gguf"


@lru_cache(maxsize=1)
def get_chatter() -> LlamaChatter:
    model_path = os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH)
    return LlamaChatter(model_path)

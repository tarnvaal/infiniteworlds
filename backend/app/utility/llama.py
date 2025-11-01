from __future__ import annotations

from typing import List, cast
from llama_cpp import (
    Llama,
    llama_log_set,
    CreateChatCompletionResponse,
    ChatCompletionRequestMessage,
)
from ctypes import CFUNCTYPE, c_int, c_char_p, c_void_p
from os.path import expanduser
from .history import History
from .gpu import get_free_vram_mib

MODEL_PATH = "~/dev/llm/Harbinger-24B-Q5_K_M.gguf"
MAX_TOKENS = 32768
TOKEN_BUFFER_SIZE = 2048
MIN_FREE_VRAM_MIB = 23400  # tune this to whatever you actually need

LOG_CB_TYPE = CFUNCTYPE(None, c_int, c_char_p, c_void_p)


def _noop_log(level, text, user_data):
    return None


_NOOP_LOG_CB = LOG_CB_TYPE(_noop_log)
llama_log_set(_NOOP_LOG_CB, None)  # type: ignore


class Chatter:
    """
    Chatter instances share one global Llama model in VRAM.
    The first Chatter() call loads it. Later Chatter() calls reuse it.
    Each instance still has its own History.
    """

    # class-level shared state
    _llm: Llama | None = None
    _init_error: Exception | None = None
    _initialized = False  # optional clarity flag

    def __init__(self, model_path: str):
        # step 1: ensure model is initialized at class level
        if not Chatter._initialized:
            Chatter._initialize_model(model_path)

        # if model init failed earlier raise now
        if Chatter._init_error is not None:
            raise RuntimeError(
                f"Failed to initialize shared Llama model: {Chatter._init_error}"
            )

        # bind the shared model handle to this instance
        # at this point _llm must be not None
        self.llm = cast(Llama, Chatter._llm)

        # step 2: per-instance setup (your old stuff)
        self.sysprompt_role = "system"
        self.display_name = "DM"
        self.sysprompt_content = (
            "You are the dungeon master. "
            "You describe the world to the player in second person present tense. "
            "You end each response with a question to the player."
        )

        self.sysprompt_tokens = self.llm.tokenize(
            self.sysprompt_content.encode("utf-8")
        )

        self.token_buffer_size = TOKEN_BUFFER_SIZE
        self.max_history_tokens = MAX_TOKENS - self.token_buffer_size

        self.history = History(
            self.max_history_tokens,
            self.sysprompt_content,
            self.sysprompt_role,
            len(self.sysprompt_tokens),
        )

    @classmethod
    def _initialize_model(cls, model_path: str) -> None:
        """
        Load the model into VRAM once.
        Safe to call multiple times. Only first call actually loads.
        """
        if cls._initialized:
            return  # already tried

        cls._initialized = True  # mark that we attempted init

        # check GPU first
        free_vram = get_free_vram_mib()
        if free_vram is None:
            cls._init_error = RuntimeError("No GPU detected. GPU is required.")
            return
        if free_vram < MIN_FREE_VRAM_MIB:
            cls._init_error = RuntimeError(
                f"Not enough VRAM free. Free VRAM: {free_vram} MiB. "
                f"Required: {MIN_FREE_VRAM_MIB} MiB."
            )
            return

        # try to actually build llama
        try:
            cls._llm = Llama(
                model_path=expanduser(model_path),
                n_ctx=MAX_TOKENS,
                n_gpu_layers=-1,  # put all layers on GPU
                n_batch=512,
                verbose=False,
            )
        except Exception as e:
            cls._init_error = e
            cls._llm = None

    def _get_token_count(self, content: str) -> int:
        try:
            tokens = self.llm.tokenize(content.encode("utf-8"))
            return len(tokens) + 5
        except Exception:
            return 10

    def chat(self, user_input: str) -> str:
        # record player message
        self.history.add_message(
            "user",
            user_input,
            self._get_token_count(user_input),
        )

        context = cast(
            List[ChatCompletionRequestMessage],
            self.history.build_context(),
        )

        raw_response = self.llm.create_chat_completion(
            messages=context,
            max_tokens=512,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stream=False,
        )

        response = cast(CreateChatCompletionResponse, raw_response)
        model_text = (
            response["choices"][0]["message"]["content"] or "[No response generated]"
        )

        # record assistant message
        self.history.add_message(
            "assistant",
            model_text,
            self._get_token_count(model_text),
        )

        return model_text


if __name__ == "__main__":
    dm = Chatter(MODEL_PATH)
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
        print(dm.chat(user_input))

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
    def __init__(self, model_path: str):
        free_vram = get_free_vram_mib()
        # GPU is required
        if free_vram is None:
            print("Error: No GPU detected. GPU is required.")
            exit(1)
        if free_vram < MIN_FREE_VRAM_MIB:
            print(
                f"Not enough VRAM free. Free VRAM: {free_vram} MiB. Required: {MIN_FREE_VRAM_MIB} MiB."
            )
            exit(1)

        try:
            self.llm = Llama(
                model_path=expanduser(model_path),
                n_ctx=MAX_TOKENS,
                n_gpu_layers=-1,  # Load all layers on GPU
                n_batch=512,
                verbose=False,
            )
        except Exception as e:
            print(f"Error: Failed to load model with all layers on GPU: {e}")
            exit(1)

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

    def _get_token_count(self, content: str) -> int:
        try:
            tokens = self.llm.tokenize(content.encode("utf-8"))
            return len(tokens) + 5
        except Exception as e:
            print(f"Error getting token count: {e}")
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

        model_text = response["choices"][0]["message"]["content"]

        # Handle empty/None responses
        if not model_text:
            model_text = "[No response generated]"

        # record assistant message (no prefix needed, frontend handles display)
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

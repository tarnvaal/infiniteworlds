from llama_cpp import Llama, llama_log_set
from ctypes import CFUNCTYPE, c_int, c_char_p, c_void_p
from os.path import expanduser
from .history import History
from .gpu import get_free_vram_mib

MODEL_PATH = "~/dev/llm/Harbinger-24B-Q5_K_M.gguf"
MAX_TOKENS = 32768

LOG_CB_TYPE = CFUNCTYPE(None, c_int, c_char_p, c_void_p)


def _noop_log(level, text, user_data):
    return None


_NOOP_LOG_CB = LOG_CB_TYPE(_noop_log)
llama_log_set(_NOOP_LOG_CB, None)

REQUIRED_VRAM_FREE = 23400


class chatter:
    def __init__(self, model_path):
        if get_free_vram_mib() < REQUIRED_VRAM_FREE:
            print(
                f"Not enough VRAM free. Required: {REQUIRED_VRAM_FREE} MiB. Free: {get_free_vram_mib()} MiB."
            )
            exit(1)
            return None
        self.llm = Llama(
            model_path=expanduser(model_path),
            n_ctx=MAX_TOKENS,
            n_gpu_layers=-1,
            n_batch=512,
            verbose=False,
        )

        self.sysprompt_role = "DM"
        self.sysprompt_content = (
            "You are a the dungeon master."
            "You describe the world to the player in second person present tense."
            "You end each response with a question to the player."
        )
        self.sysprompt_tokens = self.llm.tokenize(
            self.sysprompt_content.encode("utf-8")
        )

        self.token_buffer_size = 2048
        self.max_history_tokens = MAX_TOKENS - self.token_buffer_size

        self.history = History(
            self.max_history_tokens,
            self.sysprompt_content,
            self.sysprompt_role,
            len(self.sysprompt_tokens),
        )

    def _get_token_count(self, content: str) -> int:
        # approximate the token count.
        try:
            tokens = self.llm.tokenize(content.encode("utf-8"))
            return len(tokens) + 5
        except Exception as e:
            print(f"Error getting token count: {e}")
            return 10

    def chat(self, user_input: str) -> str:
        self.history.add_message("user", user_input, self._get_token_count(user_input))
        context = self.history.build_context()
        response = self.llm.create_chat_completion(
            messages=context,
            max_tokens=512,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        # we need to send the player a message with the assistant role first
        assistant_reply = (
            f"{self.sysprompt_role}: {response['choices'][0]['message']['content']}"
        )
        self.history.add_message(
            "assistant", assistant_reply, self._get_token_count(assistant_reply)
        )

        return assistant_reply


if __name__ == "__main__":
    chatter = chatter(MODEL_PATH)
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break
        print(f"{chatter.sysprompt_role}: {chatter.chat(user_input)}")

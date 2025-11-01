import { useMemo, useState } from "react";

function App() {
  const apiBase = useMemo(() => {
    const configured = import.meta.env.VITE_API_BASE_URL;
    if (configured) return configured;
    const host = window.location.hostname || "127.0.0.1";
    return `http://${host}:8000`;
  }, []);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;

    setHistory((h) => [...h, { role: "user", content: text }]);
    setInput("");
    setSending(true);

    const typingId = `typing-${Date.now()}`;
    setHistory((h) => [...h, { role: "assistant", type: "typing", content: "", id: typingId }]);

    try {
      const res = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) {
        let errMsg = res.statusText || "Request failed";
        try {
          const err = await res.json();
          if (err && err.detail && err.detail.message) errMsg = err.detail.message;
        } catch (_) {}
        setHistory((h) => [...h, { role: "assistant", content: `[Error] ${errMsg}` }]);
      } else {
        const data = await res.json();
        setHistory((h) => [...h, { role: "assistant", content: data.reply }]);
      }
    } catch (err) {
      setHistory((h) => [...h, { role: "assistant", content: `[Network error] ${String(err)}` }]);
    } finally {
      setHistory((h) => h.filter((m) => m.id !== typingId));
      setSending(false);
    }
  }

  async function handleClear() {
    try {
      const res = await fetch(`${apiBase}/chat/clear`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clear: true }),
      });
      if (res.ok) {
        setHistory([]);
      }
    } catch (_) {}
  }

  return (
    <div id="chat-app" className="max-w-[800px] my-4 mx-auto">
      <div className="bg-[#2C3539] border border-[#444] rounded-xl p-4 flex flex-col h-[70vh] shadow-[0_4px_12px_rgba(0,0,0,0.3)]">
        <div id="controls" className="flex gap-2 mb-2 items-center">
          <button
            className="inline-flex items-center justify-center w-9 h-9 rounded-[10px] border border-[#4a555c] bg-[#1e2a30] text-[#c9d1d9] transition-colors ease-linear hover:bg-[#26343b] hover:border-[#FF6600] hover:text-[#FF6600] active:translate-y-px"
            id="btn-clear"
            aria-label="Clear chat"
            onClick={handleClear}
            disabled={sending}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21a48.108 48.108 0 0 0-3.478-.397m-12 .397a48.108 48.108 0 0 1 3.478-.397m7.5 0V4.5A2.25 2.25 0 0 0 14.25 2.25h-4.5A2.25 2.25 0 0 0 7.5 4.5V5.79m10.5 0a48.667 48.667 0 0 1-7.5 0M5.25 6.75 4.5 19.5A2.25 2.25 0 0 0 6.75 21h10.5A2.25 2.25 0 0 0 19.5 19.5l-.75-12.75" />
            </svg>
          </button>
        </div>

        <div id="messages" className="flex-1 overflow-y-auto p-2 bg-[#1e2a30] rounded-lg mb-4 flex flex-col gap-2">
          {history.map((item, idx) => {
            if (item.type === "typing") {
              return (
                <div
                  key={item.id || idx}
                  className="px-4 py-2 my-1 rounded-[20px] max-w-[80%] leading-[1.45] font-medium text-[1.05rem] bg-[#4a555c] text-[#f1f1f1] self-start italic typing"
                >
                  DM is typing
                </div>
              );
            }
            return (
              <div
                key={idx}
                className={
                  `px-4 py-2 my-1 rounded-[20px] whitespace-pre-wrap max-w-[80%] leading-[1.45] font-medium text-[1.05rem] ` +
                  (item.role === "user"
                    ? "bg-[#FF6600] text-[#111111] self-end"
                    : "bg-[#4a555c] text-[#f1f1f1] self-start")
                }
              >
                {(item.role === "user" ? "You: " : "DM: ") + item.content}
              </div>
            );
          })}
        </div>

        <form id="chat-form" onSubmit={handleSubmit} className="flex gap-2">
          <input
            id="message-input"
            type="text"
            placeholder="Type a message and press Enter…"
            autoComplete="off"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 px-4 py-3 border border-[#4a555c] bg-[#1e2a30] text-[#f0f0f0] rounded-[20px] text-[1.05rem] font-sans placeholder:text-[#889] focus:outline-none focus:border-[#FF6600] focus:ring-2 focus:ring-[rgba(255,102,0,0.3)]"
          />
          <button
            id="send-btn"
            type="submit"
            disabled={sending || input.trim().length === 0}
            className="px-4 py-3 bg-[#FF6600] text-[#111111] rounded-[20px] cursor-pointer font-semibold text-[1rem] transition-colors hover:bg-[#FF8533] disabled:bg-[#536267] disabled:text-[#aaa] disabled:opacity-70 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;

import { useState } from "react";

function App() {
  const [userInput, setUserInput] = useState("");
  const [responseText, setResponseText] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  async function sendMessage(e) {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userInput }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(
          data?.detail?.message || data?.detail?.error || `Request failed with ${res.status}`
        );
      }

      const data = await res.json();
      setResponseText(data.reply ?? "");
      setUserInput("");
    } catch (err) {
      setErrorMsg(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: "600px", margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>Infinite Worlds</h1>
      <p style={{ fontSize: "0.9rem", color: "#666" }}>Talk to the Dungeon Master</p>

      {errorMsg && <div style={{ color: "red", marginBottom: "1rem" }}>Error: {errorMsg}</div>}

      {responseText && (
        <div
          style={{
            background: "#111",
            color: "#0f0",
            padding: "1rem",
            borderRadius: "4px",
            whiteSpace: "pre-wrap",
            fontFamily: "monospace",
          }}
        >
          {responseText}
        </div>
      )}
    </div>
  );
}

export default App;

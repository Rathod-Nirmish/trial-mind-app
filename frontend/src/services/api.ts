import type { FinalAnswer, TraceEvent } from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

type Handler = (kind: "trace" | "final", data: TraceEvent | FinalAnswer) => void;

export async function askTrialMind(question: string, onEvent: Handler): Promise<void> {
  const resp = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ question }),
  });
  if (!resp.body) throw new Error("no response body");

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Handle both \n\n and \r\n\r\n separators
    const normalized = () => buffer.replace(/\r\n/g, "\n");
    let idx: number;
    while ((idx = normalized().indexOf("\n\n")) !== -1) {
      buffer = normalized();
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);

      let eventName = "message";
      let dataLine = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith(":")) continue; // SSE comment/keepalive
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLine += line.slice(5).trim();
      }
      if (!dataLine) continue;
      try {
        const parsed = JSON.parse(dataLine);
        console.debug("[SSE]", eventName, parsed);
        if (eventName === "trace") onEvent("trace", parsed as TraceEvent);
        else if (eventName === "final") onEvent("final", parsed as FinalAnswer);
      } catch (e) {
        console.warn("[SSE] parse failed:", dataLine, e);
      }
    }
  }
}

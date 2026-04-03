"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

type Message = { role: "user" | "assistant"; content: string };

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploadStatus("Uploading...");
    const formData = new FormData();
    Array.from(files).forEach((f) => formData.append("files", f));
    const res = await fetch("/api/ingest", {
      method: "POST",
      body: formData,
    });
    const json = await res.json();
    setUploadStatus(json.message ?? "Done");
  }

  async function handleAsk() {
    if (!input.trim()) return;
    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const assistantMessage: Message = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMessage]);

    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: userMessage.content }),
    });

    if (!res.body) return;
    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      // Server-sent event (SSE) lines in format: data: token\n\n
      chunk.split("\n").forEach((line) => {
        if (line.startsWith("data: ")) {
          const token = line.slice(6);
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: updated[updated.length - 1].content + token,
            };
            return updated;
          });
        }
      });
    }
    setLoading(false);
  }

  return (
    <main className="flex flex-col items-center min-h-screen p-6 bg-background">
      <div className="w-full max-w-2xl flex flex-col gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Ask My Notes</h1>

        {/* Upload area */}
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => fileRef.current?.click()}>
            Upload notes (.txt / .md)
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept=".txt,.md"
            multiple
            className="hidden"
            onChange={handleUpload}
          />
          {uploadStatus && (
            <Badge variant="secondary">{uploadStatus}</Badge>
          )}
        </div>

        {/* Chat history */}
        <ScrollArea className="h-[420px] rounded-md border p-4 bg-muted/30">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`mb-3 text-sm ${m.role === "user" ? "text-right" : "text-left"
                }`}
            >
              <span
                className={`inline-block px-3 py-2 rounded-lg max-w-[80%] whitespace-pre-wrap ${m.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border"
                  }`}
              >
                {m.content || (loading ? "▌" : "")}
              </span>
            </div>
          ))}
          <div ref={scrollRef} />
        </ScrollArea>

        {/* Input */}
        <div className="flex gap-2">
          <Textarea
            className="resize-none"
            rows={2}
            placeholder="Ask something about your notes…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleAsk();
              }
            }}
          />
          <Button disabled={loading} onClick={handleAsk}>
            {loading ? "…" : "Ask"}
          </Button>
        </div>
      </div>
    </main>
  );
}

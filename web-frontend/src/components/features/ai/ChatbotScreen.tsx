import React from "react";
import { Bot, CornerDownLeft, RefreshCw, Sparkles, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { mlService } from "@/lib/api/mlService";
import { describeError } from "@/hooks/useAsyncData";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  actions?: string[];
  escalate?: boolean;
  failed?: boolean;
}

const SUGGESTED_PROMPTS = [
  "What's my spending this month?",
  "How can I reduce my expenses?",
  "Explain my recent transactions",
  "Set a savings goal for me",
];

export default function ChatbotScreen() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Hello! I'm your Flowlet AI assistant. I can help with spending analysis, account insights, and financial planning. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isTyping) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const reply = await mlService.chat(userMsg.content, sessionId);
      if (!isMountedRef.current) return;
      if (reply.session_id) setSessionId(reply.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: reply.response,
          timestamp: new Date(),
          actions: reply.suggested_actions,
          escalate: reply.escalate_to_human,
        },
      ]);
    } catch (err) {
      if (!isMountedRef.current) return;
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: describeError(err),
          timestamp: new Date(),
          failed: true,
        },
      ]);
    } finally {
      if (isMountedRef.current) setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage(input);
    }
  };

  const clearChat = () => {
    setSessionId(null);
    setMessages([
      {
        id: Date.now().toString(),
        role: "assistant",
        content: "Chat cleared. How can I help you?",
        timestamp: new Date(),
      },
    ]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] max-w-3xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Bot className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold">AI Assistant</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <p className="text-xs text-muted-foreground">
                Online · Powered by Flowlet AI
              </p>
            </div>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5 text-xs"
          onClick={clearChat}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Clear
        </Button>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
          {messages.length === 1 && (
            <div className="flex flex-wrap gap-2 pb-2">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => void sendMessage(prompt)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border hover:border-primary/40 hover:bg-accent/50 text-xs font-medium text-muted-foreground hover:text-foreground transition-all duration-150"
                >
                  <Sparkles className="h-3 w-3 text-primary" />
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex gap-3 animate-fade-in",
                msg.role === "user" && "flex-row-reverse",
              )}
            >
              <div
                className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5",
                  msg.role === "assistant" ? "bg-primary/10" : "bg-muted",
                )}
              >
                {msg.role === "assistant" ? (
                  <Bot className="h-4 w-4 text-primary" />
                ) : (
                  <User className="h-3.5 w-3.5 text-muted-foreground" />
                )}
              </div>
              <div
                className={cn(
                  "max-w-[75%] space-y-1",
                  msg.role === "user" && "items-end flex flex-col",
                )}
              >
                <div
                  className={cn(
                    "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                    msg.role === "assistant"
                      ? "bg-muted text-foreground rounded-tl-sm"
                      : "bg-primary text-primary-foreground rounded-tr-sm",
                    msg.failed &&
                      "border border-destructive/40 text-destructive",
                  )}
                >
                  {msg.content}
                </div>
                {msg.escalate && (
                  <Badge variant="outline" className="text-[10px]">
                    Support specialist recommended
                  </Badge>
                )}
                {msg.actions && msg.actions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {msg.actions.map((action) => (
                      <Badge
                        key={action}
                        variant="secondary"
                        className="text-[10px]"
                      >
                        {action}
                      </Badge>
                    ))}
                  </div>
                )}
                <p className="text-[10px] text-muted-foreground px-1">
                  {msg.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-3 animate-fade-in">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>

        <div className="border-t border-border p-4">
          <div className="relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything about your finances..."
              className="resize-none pr-12 min-h-[44px] max-h-32 text-sm"
              rows={1}
            />
            <Button
              size="sm"
              className="absolute right-2 bottom-2 h-8 w-8 p-0"
              disabled={!input.trim() || isTyping}
              onClick={() => void sendMessage(input)}
            >
              <CornerDownLeft className="h-3.5 w-3.5" />
            </Button>
          </div>
          <p className="text-[10px] text-muted-foreground mt-2 text-center">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      </Card>
    </div>
  );
}

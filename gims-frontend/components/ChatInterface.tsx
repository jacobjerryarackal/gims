"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send, Brain, ChevronRight, Loader2, Zap, Clock, MemoryStick,
  User, Bot, X, Sparkles, Trash2, Plus, MessageSquare
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription
} from "@/components/ui/dialog";
import { ChatMessage, Conversation, Memory, RetrievedMemory } from "@/types";
import { sendMessage, getConversations, getConversationMessages, createConversation, deleteConversation } from "@/lib/api";
import { formatRelativeDate, getScoreColor } from "@/lib/utils";
import React from "react";

const ChatMessageItem = React.memo(({ message, onMemorySelect }: { message: ChatMessage, onMemorySelect: (rm: RetrievedMemory) => void }) => {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex gap-3">
        <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          message.role === "user"
            ? "bg-primary text-primary-foreground"
            : "bg-muted border"
        }`}>
          {message.role === "user" ? (
            <User className="h-4 w-4" />
          ) : (
            <Bot className="h-4 w-4" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold">
              {message.role === "user" ? "You" : "GIMS"}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatRelativeDate(message.created_at)}
            </span>
          </div>
          <div className="prose prose-sm dark:prose-invert max-w-none markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>

          {message.retrieved_memories && message.retrieved_memories.length > 0 && (
            <div className="mt-3">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                <MemoryStick className="h-3 w-3" />
                <span>Retrieved {message.retrieved_memories.length} memory{message.retrieved_memories.length > 1 ? "ies" : "y"}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {message.retrieved_memories.map((rm) => (
                  <TooltipProvider key={rm.memory.id}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          onClick={() => onMemorySelect(rm)}
                          className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs hover:bg-accent transition-colors"
                        >
                          <Brain className="h-3 w-3 text-primary" />
                          <span className="truncate max-w-[200px]">{rm.memory.content}</span>
                          <span className={`font-mono ${getScoreColor(rm.similarity_score)}`}>
                            {(rm.similarity_score * 100).toFixed(0)}%
                          </span>
                        </button>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-xs"><p className="text-xs">{rm.explanation}</p></TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
});

export default function ChatInterface() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [selectedMemory, setSelectedMemory] = useState<RetrievedMemory | null>(null);
  const [extractedMemories, setExtractedMemories] = useState<Memory[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input when conversation changes
  useEffect(() => {
    inputRef.current?.focus();
  }, [activeConversation]);

  const loadConversations = async () => {
    try {
      const data = await getConversations();
      setConversations(data);
      if (data.length > 0 && !activeConversation) {
        setActiveConversation(data[0].id);
        loadMessages(data[0].id);
      }
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      const data = await getConversationMessages(conversationId);
      setMessages(data);
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const conversation = await createConversation();
      setConversations([conversation, ...conversations]);
      setActiveConversation(conversation.id);
      setMessages([]);
      setExtractedMemories([]);
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      const updated = conversations.filter((c) => c.id !== id);
      setConversations(updated);
      if (activeConversation === id) {
        if (updated.length > 0) {
          setActiveConversation(updated[0].id);
          loadMessages(updated[0].id);
        } else {
          setActiveConversation(null);
          setMessages([]);
        }
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    }
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversation(id);
    loadMessages(id);
    setExtractedMemories([]);
  };

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const content = input.trim();
    setInput("");
    setIsLoading(true);

    // Optimistically add user message
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await sendMessage(activeConversation, content);

      // Update conversation ID if new
      if (!activeConversation && response.conversation_id) {
        setActiveConversation(response.conversation_id);
        loadConversations();
      }

      // Add assistant message
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.response,
          created_at: new Date().toISOString(),
        },
      ]);

      // Show extracted memories
      if (response.extracted_memories && response.extracted_memories.length > 0) {
        setExtractedMemories(response.extracted_memories);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: "Sorry, I encountered an error processing your message. Please try again.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, activeConversation]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const activeConv = conversations.find((c) => c.id === activeConversation);

  return (
    <div className="flex h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* Sidebar */}
      <AnimatePresence>
        {showSidebar && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-r bg-muted/30 flex flex-col"
          >
            <div className="p-3 border-b">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={handleNewConversation}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Conversation
              </Button>
            </div>
            <ScrollArea className="flex-1">
              <div className="p-2 space-y-1">
                {conversations.length === 0 && (
                  <div className="text-center text-sm text-muted-foreground py-8">
                    <MessageSquare className="mx-auto h-8 w-8 mb-2 opacity-50" />
                    No conversations yet
                  </div>
                )}
                {conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => handleSelectConversation(conv.id)}
                    className={`w-full text-left rounded-lg px-3 py-2.5 text-sm transition-colors group relative ${
                      activeConversation === conv.id
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4 shrink-0 opacity-70" />
                      <span className="truncate flex-1">{conv.title}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-xs opacity-60">
                      <span>{conv.message_count} messages</span>
                      <span>•</span>
                      <span>{formatRelativeDate(conv.updated_at)}</span>
                    </div>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-destructive/20"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Header */}
        <div className="border-b px-4 py-3 flex items-center justify-between bg-background/95 backdrop-blur">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0"
              onClick={() => setShowSidebar(!showSidebar)}
            >
              {showSidebar ? <X className="h-4 w-4" /> : <MessageSquare className="h-4 w-4" />}
            </Button>
            <div>
              <h2 className="font-semibold text-sm">
                {activeConv?.title || "New Conversation"}
              </h2>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Badge variant="outline" className="text-[10px] h-5">
                  <Brain className="mr-1 h-3 w-3" />
                  Memory Active
                </Badge>
                {activeConv && (
                  <span>{activeConv.message_count} messages</span>
                )}
              </div>
            </div>
          </div>
          {extractedMemories.length > 0 && (
            <Badge variant="success" className="animate-pulse">
              <Sparkles className="mr-1 h-3 w-3" />
              {extractedMemories.length} new memory{extractedMemories.length > 1 ? "ies" : "y"}
            </Badge>
          )}
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 px-4" ref={scrollRef}>
          <div className="py-6 space-y-6 max-w-3xl mx-auto">
            {messages.length === 0 && !isLoading && (
              <div className="text-center py-20">
                <Brain className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-semibold mb-2">Start a conversation</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  Tell me about yourself. I will remember important facts and bring them up when relevant.
                </p>
                <div className="flex flex-wrap justify-center gap-2 mt-6">
                  {[
                    "I am an AI Engineer",
                    "I prefer first-principles explanations",
                    "I built an AI CTO Agent recently",
                  ].map((suggestion) => (
                    <Button
                      key={suggestion}
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setInput(suggestion);
                        inputRef.current?.focus();
                      }}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <React.Fragment key={message.id}>
                <ChatMessageItem message={message} onMemorySelect={setSelectedMemory} />
                {index < messages.length - 1 && <Separator className="my-6" />}
              </React.Fragment>
            ))}

            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3"
              >
                <div className="shrink-0 w-8 h-8 rounded-full bg-muted border flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <span className="text-sm text-muted-foreground">Thinking...</span>
                </div>
              </motion.div>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-4 bg-background">
          <div className="max-w-3xl mx-auto flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tell me something about yourself..."
              className="flex-1"
              disabled={isLoading}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              size="icon"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-center text-muted-foreground mt-2">
            GIMS remembers facts about you. Press Enter to send.
          </p>
        </div>
      </div>

      {/* Memory Detail Dialog */}
      <Dialog open={!!selectedMemory} onOpenChange={() => setSelectedMemory(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              Memory Details
            </DialogTitle>
            <DialogDescription>
              Why this memory was retrieved
            </DialogDescription>
          </DialogHeader>
          {selectedMemory && (
            <div className="space-y-4">
              <div className="rounded-lg bg-muted p-4">
                <p className="text-sm font-medium">{selectedMemory.memory.content}</p>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Similarity Score</span>
                  <span className={`font-mono font-bold ${getScoreColor(selectedMemory.similarity_score)}`}>
                    {(selectedMemory.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Memory Type</span>
                  <Badge variant="outline" className="capitalize">
                    {selectedMemory.memory.type}
                  </Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Quality Score</span>
                  <span className={`font-mono ${getScoreColor(selectedMemory.memory.overall_score)}`}>
                    {(selectedMemory.memory.overall_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Times Retrieved</span>
                  <span>{selectedMemory.memory.retrieval_count}</span>
                </div>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-xs font-semibold text-muted-foreground mb-1">Explanation</p>
                <p className="text-sm">{selectedMemory.explanation}</p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

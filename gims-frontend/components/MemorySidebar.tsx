"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, X, ChevronRight, Sparkles, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Memory } from "@/types";
import { getMemories } from "@/lib/api";
import { formatRelativeDate, getScoreColor } from "@/lib/utils";

interface MemorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MemorySidebar({ isOpen, onClose }: MemorySidebarProps) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      loadMemories();
    }
  }, [isOpen]);

  const loadMemories = async () => {
    setLoading(true);
    try {
      const data = await getMemories({ limit: 20 });
      setMemories(data.items);
    } catch (error) {
      console.error("Failed to load memories:", error);
    } finally {
      setLoading(false);
    }
  };

  const recentMemories = memories.slice(0, 10);
  const topMemories = [...memories]
    .sort((a, b) => b.retrieval_count - a.retrieval_count)
    .slice(0, 5);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 320, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="border-l bg-muted/30 flex flex-col h-full"
        >
          <div className="p-4 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Active Memories</h3>
            </div>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          <ScrollArea className="flex-1">
            <div className="p-4 space-y-4">
              {loading ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="h-12 bg-muted rounded animate-pulse" />
                  ))}
                </div>
              ) : (
                <>
                  {/* Recent */}
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                      Recently Added
                    </h4>
                    <div className="space-y-1">
                      {recentMemories.map((memory) => (
                        <div
                          key={memory.id}
                          className="p-2 rounded-lg bg-background border text-sm hover:shadow-sm transition-shadow"
                        >
                          <p className="line-clamp-2 text-xs leading-relaxed">{memory.content}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-[10px] capitalize">
                              {memory.type}
                            </Badge>
                            <span className="text-[10px] text-muted-foreground">
                              {formatRelativeDate(memory.created_at)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  {/* Top Retrieved */}
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                      Most Used
                    </h4>
                    <div className="space-y-1">
                      {topMemories.map((memory) => (
                        <div
                          key={memory.id}
                          className="flex items-center gap-2 p-2 rounded-lg bg-background border text-sm"
                        >
                          <TrendingUp className="h-3 w-3 text-primary shrink-0" />
                          <span className="line-clamp-1 text-xs flex-1">{memory.content}</span>
                          <span className="text-[10px] font-mono text-muted-foreground">
                            {memory.retrieval_count}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </ScrollArea>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

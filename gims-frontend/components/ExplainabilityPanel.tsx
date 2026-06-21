"use client";

import { RetrievedMemory } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, ArrowRight, Target, Sparkles } from "lucide-react";
import { getScoreColor } from "@/lib/utils";

interface ExplainabilityPanelProps {
  memories: RetrievedMemory[];
}

export function ExplainabilityPanel({ memories }: ExplainabilityPanelProps) {
  if (!memories || memories.length === 0) return null;

  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          Why These Memories Were Retrieved
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {memories.map((rm, i) => (
          <div key={rm.memory.id} className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">#{i + 1}</span>
              <Badge variant="outline" className="text-[10px] capitalize">
                {rm.memory.type}
              </Badge>
              <span className={`text-xs font-mono ${getScoreColor(rm.similarity_score)}`}>
                {(rm.similarity_score * 100).toFixed(0)}% match
              </span>
            </div>
            <p className="text-sm pl-5">{rm.explanation}</p>
            <div className="pl-5 flex items-center gap-1 text-xs text-muted-foreground">
              <Brain className="h-3 w-3" />
              <span className="truncate">{rm.memory.content}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

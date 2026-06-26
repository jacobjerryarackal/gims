"use client";

import { Memory } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, Star, TrendingUp, Clock, Edit2, Trash2 } from "lucide-react";
import { formatRelativeDate, getScoreColor, getScoreBg } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface MemoryCardProps {
  memory: Memory;
  onEdit?: (memory: Memory) => void;
  onDelete?: (memory: Memory) => void;
}

const typeConfig = {
  semantic: { icon: "👤", label: "Semantic", color: "bg-blue-500/10 text-blue-500" },
  procedural: { icon: "⚙️", label: "Procedural", color: "bg-purple-500/10 text-purple-500" },
  episodic: { icon: "📅", label: "Episodic", color: "bg-amber-500/10 text-amber-500" },
};

export function MemoryCard({ memory, onEdit, onDelete }: MemoryCardProps) {
  const config = typeConfig[memory.type];

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className={`text-xs capitalize ${config.color}`}>
                <span className="mr-1">{config.icon}</span>
                {memory.type}
              </Badge>
              <Badge
                variant="outline"
                className={`text-xs ${getScoreBg(memory.overall_score)} ${getScoreColor(memory.overall_score)}`}
              >
                <Star className="mr-1 h-3 w-3" />
                {(memory.overall_score * 100).toFixed(0)}%
              </Badge>
            </div>
            <p className="text-sm font-medium leading-relaxed">{memory.content}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatRelativeDate(memory.created_at)}
              </span>
              {memory.retrieval_count > 0 && (
                <span className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  {memory.retrieval_count} uses
                </span>
              )}
            </div>
          </div>
          {(onEdit || onDelete) && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {onEdit && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onEdit(memory)}
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
              )}
              {onDelete && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={() => onDelete(memory)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

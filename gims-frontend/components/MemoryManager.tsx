"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain, Search, Trash2, Edit2, X, Check, Filter, BarChart3,
  TrendingUp, Clock, Star, Database, Sparkles, ChevronDown, ChevronUp
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "@/components/ui/select";
import { Memory, MemoryStats } from "@/types";
import { getMemories, updateMemory, deleteMemory, getMemoryStats } from "@/lib/api";
import { formatDate, formatRelativeDate, getScoreColor, getScoreBg } from "@/lib/utils";

const typeColors = {
  semantic: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  procedural: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  episodic: "bg-amber-500/10 text-amber-500 border-amber-500/20",
};

const typeIcons = {
  semantic: "👤",
  procedural: "⚙️",
  episodic: "📅",
};

export default function MemoryManager() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Memory | null>(null);
  const [editContent, setEditContent] = useState("");
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    const loadInitialStats = async () => {
      try {
        const statsData = await getMemoryStats();
        setStats(statsData);
      } catch (error) {
        console.error("Failed to load stats:", error);
      }
    };
    loadInitialStats();
  }, [])

  useEffect(() => {
    const loadMemories = async () => {
    setLoading(true);
    try {
      const data = await getMemories({
        search: searchQuery,
        type: typeFilter === "all" ? undefined : typeFilter,
        limit: 100,
      });
      setMemories(data?.items || []); // Ensure we always set an array
      setTotalCount(data?.total || 0); // Ensure we always set a number
    } catch (error) {
        console.error("Failed to load memories:", error);
    } finally {
      setLoading(false);
    }
    };
    loadMemories();
  }, [searchQuery, typeFilter]);

  const handleUpdate = async () => {
    if (!editingMemory) return;
    try {
      await updateMemory(editingMemory.id, { content: editContent });
      setMemories((prev) =>
        prev.map((m) => (m.id === editingMemory.id ? { ...m, content: editContent } : m))
      );
      setEditingMemory(null);
    } catch (error) {
      console.error("Failed to update memory:", error);
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    try {
      await deleteMemory(deleteConfirm.id);
      setMemories((prev) => prev.filter((m) => m.id !== deleteConfirm.id));
      setTotalCount((prev) => prev - 1);
      setDeleteConfirm(null);
    } catch (error) {
      console.error("Failed to delete memory:", error);
    }
  };

  return (
    <div className="container py-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6 text-primary" />
            Memory Management
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            View, edit, and manage what GIMS knows about you
          </p>
        </div>
        <Button variant="outline" onClick={() => {}}>
          <Sparkles className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Memories</CardDescription>
              <CardTitle className="text-3xl">{totalCount}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Database className="h-3 w-3" />
                Across all types
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Semantic</CardDescription>
              <CardTitle className="text-3xl">{stats?.by_type?.semantic || 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">Facts about who you are</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Procedural</CardDescription>
              <CardTitle className="text-3xl">{stats?.by_type?.procedural || 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">Preferences and habits</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Episodic</CardDescription>
              <CardTitle className="text-3xl">{stats?.by_type?.episodic || 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xs text-muted-foreground">Events and experiences</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="list" className="space-y-4">
        <TabsList>
          <TabsTrigger value="list">
            <Brain className="mr-2 h-4 w-4" />
            All Memories
          </TabsTrigger>
          <TabsTrigger value="stats">
            <BarChart3 className="mr-2 h-4 w-4" />
            Statistics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[140px]">
                <Filter className="mr-2 h-4 w-4" />
                <SelectValue placeholder="Filter" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="semantic">Semantic</SelectItem>
                <SelectItem value="procedural">Procedural</SelectItem>
                <SelectItem value="episodic">Episodic</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Memory List */}
          <div className="space-y-2">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <Skeleton className="h-4 w-3/4 mb-2" />
                    <Skeleton className="h-3 w-1/2" />
                  </CardContent>
                </Card>
              )) // Use memories directly, as they are now always filtered by the server
            ) : memories.length === 0 ? (
              <div className="text-center py-12">
                <Brain className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="text-lg font-semibold">No memories found</h3>
                <p className="text-sm text-muted-foreground">
                  Start chatting to create memories, or try a different search.
                </p>
              </div>
            ) : (
              memories.map((memory) => (
                <motion.div
                  key={memory.id}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <Card className="group hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge
                              variant="outline"
                              className={`text-xs capitalize ${typeColors[memory.type]}`}
                            >
                              <span className="mr-1">{typeIcons[memory.type]}</span>
                              {memory.type}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={`text-xs ${getScoreBg(memory.overall_score)} ${getScoreColor(memory.overall_score)}`}
                            >
                              <Star className="mr-1 h-3 w-3" />
                              {(memory.overall_score * 100).toFixed(0)}%
                            </Badge>
                            {memory.retrieval_count > 0 && (
                              <Badge variant="outline" className="text-xs">
                                <TrendingUp className="mr-1 h-3 w-3" />
                                {memory.retrieval_count} uses
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm font-medium leading-relaxed">{memory.content}</p>
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              Created {formatRelativeDate(memory.created_at)}
                            </span>
                            {memory.last_retrieved_at && (
                              <span className="flex items-center gap-1">
                                <TrendingUp className="h-3 w-3" />
                                Last used {formatRelativeDate(memory.last_retrieved_at)}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => {
                              setEditingMemory(memory);
                              setEditContent(memory.content);
                            }}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:text-destructive"
                            onClick={() => setDeleteConfirm(memory)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="stats" className="space-y-4">
          {stats && (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Quality Distribution</CardTitle>
                  <CardDescription>Memories by overall quality score</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {Object.entries(stats?.by_score_range || {}).map(([range, count]) => (
                    <div key={range}>
                      <div className="flex justify-between text-sm mb-1">
                        <span>{range}</span>
                        <span className="font-mono">{count}</span>
                      </div>
                      <Progress
                        value={totalCount > 0 ? (count / totalCount) * 100 : 0}
                        className="h-2"
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recently Added</CardTitle>
                  <CardDescription>Latest memories created</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {(stats?.recently_added || []).slice(0, 5).map((memory) => (
                    <div
                      key={memory.id}
                      className="flex items-center gap-2 p-2 rounded-lg hover:bg-accent transition-colors"
                    >
                      <Badge variant="outline" className={`text-[10px] capitalize ${typeColors[memory.type]}`}>
                        {memory.type}
                      </Badge>
                      <span className="text-sm truncate flex-1">{memory.content}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatRelativeDate(memory.created_at)}
                      </span>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>Top Retrieved Memories</CardTitle>
                  <CardDescription>Most frequently used memories</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-2 md:grid-cols-2">
                    {(stats?.top_retrieved || []).slice(0, 6).map((memory) => (
                      <div
                        key={memory.id}
                        className="flex items-center gap-3 p-3 rounded-lg border"
                      >
                        <div className="shrink-0">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <TrendingUp className="h-5 w-5 text-primary" />
                          </div>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium truncate">{memory.content}</p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{memory.retrieval_count} retrievals</span>
                            <span>•</span>
                            <span className="capitalize">{memory.type}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={!!editingMemory} onOpenChange={() => setEditingMemory(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Memory</DialogTitle>
            <DialogDescription>Update the content of this memory</DialogDescription>
          </DialogHeader>
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingMemory(null)}>
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>
            <Button onClick={handleUpdate}>
              <Check className="mr-2 h-4 w-4" />
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-destructive">Delete Memory</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this memory? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {deleteConfirm && (
            <div className="rounded-lg bg-muted p-3 text-sm">
              {deleteConfirm.content}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

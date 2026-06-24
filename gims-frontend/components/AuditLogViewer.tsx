"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ClipboardList, Search, Filter, Clock, User, Database,
  Plus, Pencil, Trash2, Eye, Search as SearchIcon, CheckCircle, XCircle, Sparkles
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "@/components/ui/select";
import { AuditLog } from "@/types";
import { getAuditLogs } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const operationConfig = {
  create: { icon: Plus, color: "text-emerald-500", bg: "bg-emerald-500/10", label: "Created" },
  update: { icon: Pencil, color: "text-blue-500", bg: "bg-blue-500/10", label: "Updated" },
  delete: { icon: Trash2, color: "text-red-500", bg: "bg-red-500/10", label: "Deleted" },
  retrieve: { icon: Eye, color: "text-purple-500", bg: "bg-purple-500/10", label: "Retrieved" },
  evaluate: { icon: CheckCircle, color: "text-amber-500", bg: "bg-amber-500/10", label: "Evaluated" },
  extract: { icon: SearchIcon, color: "text-cyan-500", bg: "bg-cyan-500/10", label: "Extracted" },
};

export default function AuditLogViewer() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [operationFilter, setOperationFilter] = useState<string>("all");
  const [page, setPage] = useState(0);
  const pageSize = 50;

  useEffect(() => {
    loadLogs();
  }, [page, operationFilter]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await getAuditLogs({
        operation: operationFilter === "all" ? undefined : operationFilter,
        limit: pageSize,
        offset: page * pageSize,
      });
      setLogs(data.items);
      setTotalCount(data.total);
    } catch (error) {
      console.error("Failed to load audit logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(0);
    loadLogs();
  };

  const filteredLogs = (logs || []).filter((log) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        log.action.toLowerCase().includes(q) ||
        log.user_id?.toLowerCase().includes(q) ||
        log.reason.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="container py-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ClipboardList className="h-6 w-6 text-primary" />
            Audit Log
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Complete record of all memory operations for compliance and debugging
          </p>
        </div>
        <Button variant="outline" onClick={loadLogs}>
          <Sparkles className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-6 mb-6">
        {Object.entries(operationConfig).map(([op, config]) => {
          const count = logs.filter((l) => l.action === op).length;
          return (
            <Card key={op}>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <div className={`p-2 rounded-lg ${config.bg}`}>
                    <config.icon className={`h-4 w-4 ${config.color}`} />
                  </div>
                  <div>
                    <div className="text-2xl font-bold">{count}</div>
                    <div className="text-xs text-muted-foreground">{config.label}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="pl-9"
          />
        </div>
        <Select value={operationFilter} onValueChange={setOperationFilter}>
          <SelectTrigger className="w-[160px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Filter" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Operations</SelectItem>
            <SelectItem value="create">Create</SelectItem>
            <SelectItem value="update">Update</SelectItem>
            <SelectItem value="delete">Delete</SelectItem>
            <SelectItem value="retrieve">Retrieve</SelectItem>
            <SelectItem value="evaluate">Evaluate</SelectItem>
            <SelectItem value="extract">Extract</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={handleSearch}>Search</Button>
      </div>

      {/* Log Table */}
      <Card>
        <CardContent className="p-0">
          <ScrollArea className="h-[600px]">
            <div className="min-w-[800px]">
              <div className="grid grid-cols-[120px_1fr_120px_200px] gap-4 px-4 py-3 border-b bg-muted/50 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <div>Operation</div>
                <div>Details</div>
                <div>Memory ID</div>
                <div>Timestamp</div>
              </div>

              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="grid grid-cols-[120px_1fr_120px_200px] gap-4 px-4 py-4 border-b">
                    <Skeleton className="h-5 w-20" />
                    <Skeleton className="h-5 w-3/4" />
                    <Skeleton className="h-5 w-24" />
                    <Skeleton className="h-5 w-32" />
                  </div>
                ))
              ) : filteredLogs.length === 0 ? (
                <div className="text-center py-12">
                  <ClipboardList className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-semibold">No audit logs found</h3>
                  <p className="text-sm text-muted-foreground">
                    Operations will appear here once the system processes memories.
                  </p>
                </div>
              ) : (
                filteredLogs.map((log, i) => {
                  const config =operationConfig[ log.action as keyof typeof operationConfig ] || operationConfig.extract;
                  return (
                    <motion.div
                      key={log.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className="grid grid-cols-[120px_1fr_120px_200px] gap-4 px-4 py-4 border-b hover:bg-accent/50 transition-colors items-start"
                    >
                      <div>
                        <Badge variant="outline" className={`text-xs ${config.bg} ${config.color} border-0`}>
                          <config.icon className="mr-1 h-3 w-3" />
                          {config.label}
                        </Badge>
                      </div>
                      <div className="text-sm">
                        <div className="text-sm">
                          {log.reason}
                        </div>
                      </div>
                      <div className="text-xs font-mono text-muted-foreground">
                        {log.user_id
                          ? log.user_id.slice(0, 8) + "..."
                          : "—"}
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(log.created_at)}
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>
          </ScrollArea>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {page * pageSize + 1} to {Math.min((page + 1) * pageSize, totalCount)} of {totalCount} entries
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

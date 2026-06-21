"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Activity, Database, Server, AlertTriangle, CheckCircle, XCircle,
  TrendingUp, TrendingDown, Minus, Brain, MessageSquare, Clock, Sparkles
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { SystemMetrics } from "@/types";
import { getMetrics } from "@/lib/api";

const statusConfig = {
  healthy: { icon: CheckCircle, color: "text-emerald-500", bg: "bg-emerald-500/10", label: "Healthy" },
  degraded: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-500/10", label: "Degraded" },
  down: { icon: XCircle, color: "text-red-500", bg: "bg-red-500/10", label: "Down" },
};

export default function HealthDashboard() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await getMetrics();
      setMetrics(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to load metrics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container py-6 max-w-6xl">
        <div className="grid gap-4 md:grid-cols-3 mb-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-8 w-32 mb-2" />
                <Skeleton className="h-12 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="container py-6 max-w-6xl text-center">
        <Activity className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-semibold">Unable to load metrics</h3>
        <p className="text-sm text-muted-foreground">The system may be unavailable.</p>
      </div>
    );
  }

  const services = [
    { name: "API Service", ...metrics.api_health },
    { name: "PostgreSQL", ...metrics.db_health },
    { name: "ChromaDB", ...metrics.vector_db_health },
  ];

  return (
    <div className="container py-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            System Health
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time monitoring of GIMS performance and health
          </p>
        </div>
        <div className="text-xs text-muted-foreground">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </div>
      </div>

      {/* Service Status */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        {services.map((service) => {
          const config = statusConfig[service.status];
          return (
            <motion.div
              key={service.name}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${config.bg}`}>
                        <config.icon className={`h-5 w-5 ${config.color}`} />
                      </div>
                      <div>
                        <div className="font-semibold">{service.name}</div>
                        <div className="text-xs text-muted-foreground">{service.latency_ms}ms latency</div>
                      </div>
                    </div>
                    <Badge variant="outline" className={`${config.bg} ${config.color} border-0`}>
                      {config.label}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Memories</CardDescription>
            <CardTitle className="text-3xl flex items-center gap-2">
              <Brain className="h-6 w-6 text-primary" />
              {metrics.total_memories.toLocaleString()}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Conversations</CardDescription>
            <CardTitle className="text-3xl flex items-center gap-2">
              <MessageSquare className="h-6 w-6 text-primary" />
              {metrics.total_conversations.toLocaleString()}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Messages</CardDescription>
            <CardTitle className="text-3xl flex items-center gap-2">
              <Database className="h-6 w-6 text-primary" />
              {metrics.total_messages.toLocaleString()}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Pending Reviews</CardDescription>
            <CardTitle className="text-3xl flex items-center gap-2">
              <Clock className="h-6 w-6 text-primary" />
              {metrics.pending_reviews}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Quality Metrics */}
      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Memory Quality</CardTitle>
            <CardDescription>Precision and recall metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Precision</span>
                <span className="font-mono">{(metrics.memory_precision * 100).toFixed(1)}%</span>
              </div>
              <Progress value={metrics.memory_precision * 100} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Recall</span>
                <span className="font-mono">{(metrics.memory_recall * 100).toFixed(1)}%</span>
              </div>
              <Progress value={metrics.memory_recall * 100} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Duplicate Detection</span>
                <span className="font-mono">{(metrics.duplicate_detection_rate * 100).toFixed(1)}%</span>
              </div>
              <Progress value={metrics.duplicate_detection_rate * 100} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance</CardTitle>
            <CardDescription>System response metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-muted">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-primary" />
                <span className="text-sm">Avg Retrieval Time</span>
              </div>
              <span className="font-mono font-semibold">{metrics.avg_retrieval_time_ms.toFixed(0)}ms</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-muted">
              <div className="flex items-center gap-2">
                <Server className="h-4 w-4 text-primary" />
                <span className="text-sm">API Latency</span>
              </div>
              <span className="font-mono font-semibold">{metrics.api_health.latency_ms}ms</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-muted">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-primary" />
                <span className="text-sm">DB Latency</span>
              </div>
              <span className="font-mono font-semibold">{metrics.db_health.latency_ms}ms</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

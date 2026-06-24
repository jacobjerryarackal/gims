"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle, XCircle, Eye, Clock, Brain, Sparkles, Filter, Search
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "@/components/ui/dialog";
import { HITLReview } from "@/types";
import { getHITLQueue, reviewHITLItem } from "@/lib/api";
import { formatDate, getScoreColor, getScoreBg } from "@/lib/utils";

export default function HITLPage() {
  const [reviews, setReviews] = useState<HITLReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReview, setSelectedReview] = useState<HITLReview | null>(null);
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadReviews();
  }, []);

  const loadReviews = async () => {
    setLoading(true);
    try {
      const data = await getHITLQueue();
      setReviews(data.items);
    } catch (error) {
      console.error("Failed to load reviews:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (status: "approved" | "rejected") => {
    if (!selectedReview) return;
    setProcessing(true);
    try {
      await reviewHITLItem(
        selectedReview.id,
        status === "approved"
          ? "approve"
          : "reject",
        reviewerNotes
      );
      setReviews((prev) => prev.filter((r) => r.id !== selectedReview.id));
      setSelectedReview(null);
      setReviewerNotes("");
    } catch (error) {
      console.error("Failed to review:", error);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="container py-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Eye className="h-6 w-6 text-primary" />
            Human Review Queue
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Review and approve memories that did not pass the automatic quality gate
          </p>
        </div>
        <Button variant="outline" onClick={loadReviews}>
          <Sparkles className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <Clock className="h-5 w-5 text-amber-500" />
              </div>
              <div>
                <div className="text-2xl font-bold">{reviews.length}</div>
                <div className="text-xs text-muted-foreground">Pending Reviews</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Review List */}
      <div className="space-y-2">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <Skeleton className="h-4 w-3/4 mb-2" />
                <Skeleton className="h-3 w-1/2" />
              </CardContent>
            </Card>
          ))
        ) : reviews.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle className="mx-auto h-12 w-12 text-emerald-500/50 mb-4" />
            <h3 className="text-lg font-semibold">All caught up!</h3>
            <p className="text-sm text-muted-foreground">
              No pending reviews in the queue.
            </p>
          </div>
        ) : (
          reviews.map((review, i) => (
            <motion.div
              key={review.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => setSelectedReview(review)}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="text-xs capitalize">
                          {review.status}
                        </Badge>
                        <Badge
                          variant="outline"
                          className={`text-xs ${getScoreBg(review.confidence_score || 0.5)} ${getScoreColor(review.confidence_score || 0.5)}`}
                        >
                          Confidence: {((review.confidence_score || 0.5) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <p className="text-sm font-medium">{review.memory_content}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <span>Created {formatDate(review.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-emerald-500 hover:text-emerald-600 hover:bg-emerald-500/10"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedReview(review);
                        }}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))
        )}
      </div>

      {/* Review Dialog */}
      <Dialog open={!!selectedReview} onOpenChange={() => { setSelectedReview(null); setReviewerNotes(""); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Review Memory</DialogTitle>
            <DialogDescription>
              Approve or reject this memory for storage
            </DialogDescription>
          </DialogHeader>
          {selectedReview && (
            <div className="space-y-4">
              <div className="rounded-lg bg-muted p-4">
                <p className="text-sm font-medium">{selectedReview.memory_content}</p>
              </div>
              <div className="rounded-lg border p-3">
                <div className="text-sm text-muted-foreground">
                  Confidence Score
                </div>
                <div className="text-lg font-bold">
                  {(selectedReview.confidence_score * 100).toFixed(0)}%
                </div>
              </div>
              <Textarea
                placeholder="Add reviewer notes (optional)..."
                value={reviewerNotes}
                onChange={(e) => setReviewerNotes(e.target.value)}
              />
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => handleReview("rejected")}
              disabled={processing}
              className="text-red-500 hover:text-red-600"
            >
              <XCircle className="mr-2 h-4 w-4" />
              Reject
            </Button>
            <Button
              onClick={() => handleReview("approved")}
              disabled={processing}
              className="bg-emerald-500 hover:bg-emerald-600"
            >
              <CheckCircle className="mr-2 h-4 w-4" />
              Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

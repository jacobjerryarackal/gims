"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Brain, MessageSquare, Shield, Sparkles, ArrowRight, Database, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LandingPage() {
  const router = useRouter();

  const features = [
    {
      icon: Brain,
      title: "Persistent Memory",
      description: "The system learns facts about you and remembers them across every conversation.",
    },
    {
      icon: Shield,
      title: "Quality Gates",
      description: "Every memory is evaluated for relevance, novelty, and accuracy before storage.",
    },
    {
      icon: Eye,
      title: "Explainability",
      description: "Understand exactly why a memory was retrieved with detailed explanations.",
    },
    {
      icon: Database,
      title: "Full Control",
      description: "View, edit, or delete any memory. Complete audit trail of all operations.",
    },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="flex items-center gap-2 font-bold text-xl">
            <Sparkles className="h-6 w-6 text-primary" />
            <span>GIMS</span>
          </div>
          <nav className="ml-auto flex gap-4 items-center">
            <Button variant="ghost" onClick={() => router.push("/memories")}>Memories</Button>
            <Button variant="ghost" onClick={() => router.push("/audit")}>Audit</Button>
            <Button onClick={() => router.push("/chat")}>
              <MessageSquare className="mr-2 h-4 w-4" />
              Start Chatting
            </Button>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1">
        <section className="container py-24 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mx-auto max-w-3xl text-center"
          >
            <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium mb-6">
              <Sparkles className="mr-1 h-3 w-3 text-primary" />
              GPT Intelligence Memory System
            </div>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl mb-6">
              Conversations that{" "}
              <span className="text-primary">remember</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Unlike regular chatbots that forget everything when you start a new chat, 
              GIMS learns, stores, and recalls what matters about you across every conversation.
            </p>
            <div className="flex justify-center gap-4">
              <Button size="lg" onClick={() => router.push("/chat")}>
                Start Chatting
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button size="lg" variant="outline" onClick={() => router.push("/memories")}>
                Explore Memories
              </Button>
            </div>
          </motion.div>
        </section>

        {/* Features */}
        <section className="container pb-24">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <feature.icon className="h-8 w-8 text-primary mb-2" />
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-sm leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Memory Types */}
        <section className="container pb-24">
          <div className="mx-auto max-w-3xl text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tight mb-4">Three Types of Memory</h2>
            <p className="text-muted-foreground">
              GIMS captures different kinds of information to build a complete picture of you.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              { type: "Semantic", desc: "Facts about who you are", example: "I am an AI Engineer" },
              { type: "Procedural", desc: "How you like things done", example: "I prefer first-principles explanations" },
              { type: "Episodic", desc: "Specific events and experiences", example: "I built an AI CTO Agent in January" },
            ].map((item, i) => (
              <motion.div
                key={item.type}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
              >
                <Card className="border-l-4 border-l-primary">
                  <CardHeader>
                    <CardTitle>{item.type}</CardTitle>
                    <CardDescription>{item.desc}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-lg bg-muted p-3 text-sm font-mono">
                      {item.example}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-6">
        <div className="container flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            <span className="font-semibold">GIMS</span>
          </div>
          <p>Built by Jacob</p>
        </div>
      </footer>
    </div>
  );
}

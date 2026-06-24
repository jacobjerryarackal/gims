"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Brain,
  MessageSquare,
  Shield,
  Sparkles,
  ArrowRight,
  Database,
  Eye,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LandingPage() {
  const router = useRouter();

  const features = [
    {
      icon: Brain,
      title: "Persistent Memory",
      description:
        "The system learns facts about you and remembers them across every conversation.",
    },
    {
      icon: Shield,
      title: "Quality Gates",
      description:
        "Every memory is evaluated for relevance, novelty, and accuracy before storage.",
    },
    {
      icon: Eye,
      title: "Explainability",
      description:
        "Understand exactly why a memory was retrieved with detailed explanations.",
    },
    {
      icon: Database,
      title: "Full Control",
      description:
        "View, edit, or delete any memory. Complete audit trail of all operations.",
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* HEADER */}
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center px-6 lg:px-8">
          <div className="flex items-center gap-2 font-bold text-2xl">
            <Sparkles className="h-6 w-6 text-primary" />
            <span>GIMS</span>
          </div>

          <nav className="ml-auto flex items-center gap-2">
            <Button
              variant="ghost"
              onClick={() => router.push("/memories")}
            >
              Memories
            </Button>

            <Button
              variant="ghost"
              onClick={() => router.push("/audit")}
            >
              Audit
            </Button>

            <Button onClick={() => router.push("/chat")}>
              <MessageSquare className="mr-2 h-4 w-4" />
              Start Chatting
            </Button>
          </nav>
        </div>
      </header>

      {/* HERO */}
      <main>
        <section className="mx-auto max-w-7xl px-6 py-28 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mx-auto max-w-4xl text-center"
          >
            <div className="mb-8 inline-flex items-center rounded-full border px-4 py-2 text-sm font-medium">
              <Sparkles className="mr-2 h-4 w-4 text-primary" />
              GPT Intelligence Memory System
            </div>

            <h1 className="mb-8 text-5xl font-bold tracking-tight md:text-7xl">
              Conversations that{" "}
              <span className="text-primary">remember</span>
            </h1>

            <p className="mx-auto mb-10 max-w-3xl text-xl text-muted-foreground">
              Unlike regular chatbots that forget everything when you start a
              new chat, GIMS learns, stores, and recalls what matters about you
              across every conversation.
            </p>

            <div className="flex flex-col justify-center gap-4 sm:flex-row">
              <Button
                size="lg"
                onClick={() => router.push("/chat")}
              >
                Start Chatting
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>

              <Button
                size="lg"
                variant="outline"
                onClick={() => router.push("/memories")}
              >
                Explore Memories
              </Button>
            </div>
          </motion.div>
        </section>

        {/* FEATURES */}
        <section className="mx-auto max-w-7xl px-6 pb-28 lg:px-8">
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  delay: i * 0.1,
                  duration: 0.5,
                }}
              >
                <Card className="h-full transition-all hover:shadow-lg">
                  <CardHeader>
                    <feature.icon className="mb-3 h-8 w-8 text-primary" />

                    <CardTitle>
                      {feature.title}
                    </CardTitle>
                  </CardHeader>

                  <CardContent>
                    <CardDescription className="leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>

        {/* MEMORY TYPES */}
        <section className="mx-auto max-w-7xl px-6 pb-32 lg:px-8">
          <div className="mx-auto mb-14 max-w-3xl text-center">
            <h2 className="mb-4 text-4xl font-bold">
              Three Types of Memory
            </h2>

            <p className="text-lg text-muted-foreground">
              GIMS captures different kinds of information to build a complete
              picture of you.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            {[
              {
                type: "Semantic",
                desc: "Facts about who you are",
                example: "I am an AI Engineer",
              },
              {
                type: "Procedural",
                desc: "How you like things done",
                example:
                  "I prefer first-principles explanations",
              },
              {
                type: "Episodic",
                desc: "Specific events and experiences",
                example:
                  "I built an AI CTO Agent in January",
              },
            ].map((item, i) => (
              <motion.div
                key={item.type}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{
                  delay: i * 0.1,
                  duration: 0.4,
                }}
              >
                <Card className="h-full border-l-4 border-l-primary">
                  <CardHeader>
                    <CardTitle>{item.type}</CardTitle>

                    <CardDescription>
                      {item.desc}
                    </CardDescription>
                  </CardHeader>

                  <CardContent>
                    <div className="rounded-lg bg-muted p-4 font-mono text-sm">
                      {item.example}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>
      </main>

      {/* FOOTER */}
      <footer className="border-t">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-8 lg:px-8">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4" />
            <span className="font-semibold">GIMS</span>
          </div>

          <p className="text-sm text-muted-foreground">
            Built by Jacob
          </p>
        </div>
      </footer>
    </div>
  );
}
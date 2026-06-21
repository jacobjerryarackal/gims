import { Navigation } from "@/components/navigation";
import ChatInterface from "@/components/ChatInterface";

export default function ChatPage() {
  return (
    <div className="flex flex-col h-screen">
      <Navigation />
      <ChatInterface />
    </div>
  );
}

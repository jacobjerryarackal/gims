import { Navigation } from "@/components/navigation";
import MemoryManager from "@/components/MemoryManager";

export default function MemoriesPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Navigation />
      <main className="flex-1">
        <MemoryManager />
      </main>
    </div>
  );
}

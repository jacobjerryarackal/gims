import { Navigation } from "@/components/navigation";
import AuditLogViewer from "@/components/AuditLogViewer";

export default function AuditPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Navigation />
      <main className="flex-1">
        <AuditLogViewer />
      </main>
    </div>
  );
}

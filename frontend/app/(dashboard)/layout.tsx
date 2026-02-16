import { ReactNode } from "react";
import { TopNav } from "@/components/top-nav";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <main className="mx-auto min-h-screen max-w-6xl space-y-6 px-6 py-8">
      <header className="space-y-3">
        <h1 className="text-2xl font-semibold text-brand-900">Dashboard</h1>
        <TopNav />
      </header>
      {children}
    </main>
  );
}


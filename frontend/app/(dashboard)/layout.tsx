"use client";

import { ReactNode, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/api";
import { TopNav } from "@/components/top-nav";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/");
    } else {
      setChecked(true);
    }
  }, [router]);

  if (!checked) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-slate-500">Checking authentication…</p>
      </main>
    );
  }

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

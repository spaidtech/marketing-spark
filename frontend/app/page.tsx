"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function HomePage() {
  const [email, setEmail] = useState("founder@example.com");
  const [error, setError] = useState("");
  const router = useRouter();

  async function loginDev() {
    try {
      setError("");
      const data = await api.devToken(email);
      localStorage.setItem("jwt", data.access_token);
      router.push("/campaigns");
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl items-center px-6">
      <section className="w-full rounded-3xl bg-white/80 p-10 shadow-xl">
        <h1 className="text-3xl font-bold text-brand-900">AI Marketing Asset Engine</h1>
        <p className="mt-3 text-sm text-brand-700">
          Dev login is enabled. Replace this with Google OAuth in production.
        </p>
        <div className="mt-6 space-y-3">
          <input
            className="w-full rounded-xl border border-brand-200 px-4 py-3"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button
            onClick={loginDev}
            className="w-full rounded-xl bg-brand-500 px-4 py-3 font-medium text-white"
          >
            Continue to Dashboard
          </button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      </section>
    </main>
  );
}


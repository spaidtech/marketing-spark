"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [form, setForm] = useState({ name: "", goal: "", audience: "" });

  async function load() {
    const data = await api.listCampaigns();
    setCampaigns(data);
  }

  async function createCampaign(e: React.FormEvent) {
    e.preventDefault();
    await api.createCampaign(form);
    setForm({ name: "", goal: "", audience: "" });
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <section className="grid gap-6 md:grid-cols-2">
      <form className="rounded-2xl bg-white p-6 shadow" onSubmit={createCampaign}>
        <h2 className="text-lg font-semibold">Create Campaign</h2>
        <div className="mt-4 space-y-3">
          <input
            className="w-full rounded-lg border px-3 py-2"
            placeholder="Campaign name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <textarea
            className="w-full rounded-lg border px-3 py-2"
            placeholder="Goal"
            value={form.goal}
            onChange={(e) => setForm({ ...form, goal: e.target.value })}
            required
          />
          <textarea
            className="w-full rounded-lg border px-3 py-2"
            placeholder="Audience"
            value={form.audience}
            onChange={(e) => setForm({ ...form, audience: e.target.value })}
            required
          />
          <button className="rounded-lg bg-brand-500 px-4 py-2 text-white">Create</button>
        </div>
      </form>

      <div className="rounded-2xl bg-white p-6 shadow">
        <h2 className="text-lg font-semibold">Your Campaigns</h2>
        <ul className="mt-4 space-y-3">
          {campaigns.map((c) => (
            <li key={c.id} className="rounded-lg border p-3">
              <p className="font-medium">{c.name}</p>
              <p className="text-sm text-slate-600">{c.goal}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}


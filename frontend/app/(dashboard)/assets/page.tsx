"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function AssetsPage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [form, setForm] = useState({ campaign_id: 1, asset_type: "ad_copy", title: "", content: "" });
  const [selected, setSelected] = useState<any | null>(null);
  const [updatedContent, setUpdatedContent] = useState("");

  async function load() {
    const data = await api.listAssets();
    setAssets(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function createAsset(e: React.FormEvent) {
    e.preventDefault();
    await api.createAsset(form);
    setForm({ ...form, title: "", content: "" });
    await load();
  }

  async function saveEdit() {
    if (!selected) return;
    await api.updateAsset(selected.id, { content: updatedContent, change_note: "dashboard_edit" });
    setSelected(null);
    setUpdatedContent("");
    await load();
  }

  return (
    <section className="grid gap-6 md:grid-cols-2">
      <form className="rounded-2xl bg-white p-6 shadow" onSubmit={createAsset}>
        <h2 className="text-lg font-semibold">Create Asset</h2>
        <div className="mt-4 space-y-3">
          <input
            className="w-full rounded-lg border px-3 py-2"
            placeholder="Title"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
          />
          <textarea
            className="w-full rounded-lg border px-3 py-2"
            placeholder="Initial content"
            value={form.content}
            onChange={(e) => setForm({ ...form, content: e.target.value })}
          />
          <button className="rounded-lg bg-brand-500 px-4 py-2 text-white">Create Asset</button>
        </div>
      </form>

      <div className="rounded-2xl bg-white p-6 shadow">
        <h2 className="text-lg font-semibold">Assets</h2>
        <ul className="mt-4 space-y-3">
          {assets.map((a) => (
            <li key={a.id} className="rounded-lg border p-3">
              <p className="font-medium">
                {a.title} <span className="text-xs text-slate-500">(v{a.current_version})</span>
              </p>
              <p className="line-clamp-2 text-sm text-slate-600">{a.content}</p>
              <button
                className="mt-2 rounded bg-brand-100 px-3 py-1 text-sm text-brand-700"
                onClick={() => {
                  setSelected(a);
                  setUpdatedContent(a.content);
                }}
              >
                Edit
              </button>
            </li>
          ))}
        </ul>
      </div>

      {selected && (
        <div className="md:col-span-2 rounded-2xl bg-white p-6 shadow">
          <h3 className="text-lg font-semibold">Edit: {selected.title}</h3>
          <textarea
            className="mt-3 min-h-40 w-full rounded-lg border px-3 py-2"
            value={updatedContent}
            onChange={(e) => setUpdatedContent(e.target.value)}
          />
          <button className="mt-3 rounded-lg bg-brand-500 px-4 py-2 text-white" onClick={saveEdit}>
            Save New Version
          </button>
        </div>
      )}
    </section>
  );
}


"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function AIStudioPage() {
  const [campaignId, setCampaignId] = useState(1);
  const [prompt, setPrompt] = useState("Launch a SaaS landing page for startup founders.");
  const [copy, setCopy] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [balance, setBalance] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function runText() {
    try {
      setError("");
      const data = await api.generateText({ campaign_id: campaignId, prompt, tone: "bold", channel: "landing_page" });
      setCopy(data.content);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function runImage() {
    try {
      setError("");
      const data = await api.generateImage({ campaign_id: campaignId, prompt, style: "modern", width: 1024, height: 1024 });
      setImageUrl(data.image_url);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function runSuggestions() {
    const data = await api.suggestions({ campaign_id: campaignId, asset_text: copy || prompt });
    setSuggestions(data.suggestions);
  }

  async function loadBalance() {
    const data = await api.balance();
    setBalance(data.balance);
  }

  return (
    <section className="space-y-6">
      <div className="rounded-2xl bg-white p-6 shadow">
        <h2 className="text-lg font-semibold">AI Studio</h2>
        <div className="mt-4 grid gap-3">
          <input
            className="rounded-lg border px-3 py-2"
            type="number"
            value={campaignId}
            onChange={(e) => setCampaignId(Number(e.target.value))}
          />
          <textarea
            className="rounded-lg border px-3 py-2"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <div className="flex flex-wrap gap-2">
            <button className="rounded-lg bg-brand-500 px-4 py-2 text-white" onClick={runText}>Generate Text</button>
            <button className="rounded-lg bg-brand-700 px-4 py-2 text-white" onClick={runImage}>Generate Image</button>
            <button className="rounded-lg bg-brand-100 px-4 py-2 text-brand-700" onClick={runSuggestions}>Optimize Suggestions</button>
            <button className="rounded-lg border px-4 py-2" onClick={loadBalance}>Check Credits</button>
          </div>
          {balance !== null && <p className="text-sm">Credits balance: <strong>{balance}</strong></p>}
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <article className="rounded-2xl bg-white p-6 shadow">
          <h3 className="font-semibold">Generated Copy</h3>
          <p className="mt-3 whitespace-pre-wrap text-sm">{copy || "No generated text yet."}</p>
        </article>
        <article className="rounded-2xl bg-white p-6 shadow">
          <h3 className="font-semibold">Generated Image</h3>
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={imageUrl} alt="Generated creative" className="mt-3 rounded-xl border" />
          ) : (
            <p className="mt-3 text-sm">No generated image yet.</p>
          )}
        </article>
      </div>

      <article className="rounded-2xl bg-white p-6 shadow">
        <h3 className="font-semibold">Conversion Suggestions</h3>
        <ul className="mt-3 list-disc pl-5 text-sm">
          {suggestions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>
    </section>
  );
}


import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function devToken(email: string) {
  const res = await fetch(`${API_BASE}/api/v1/dev-token?email=${encodeURIComponent(email)}`, { method: "POST" });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

function App() {
  const [jwt, setJwt] = useState(() => localStorage.getItem("jwt"));
  const [email, setEmail] = useState("founder@example.com");
  const [error, setError] = useState("");
  const [view, setView] = useState<"campaigns" | "assets" | "ai-studio">("campaigns");

  async function loginDev() {
    try {
      setError("");
      const data = await devToken(email);
      localStorage.setItem("jwt", data.access_token);
      setJwt(data.access_token);
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  }

  function logout() {
    localStorage.removeItem("jwt");
    setJwt(null);
  }

  if (!jwt) {
    return (
      <main className="mx-auto flex min-h-screen max-w-2xl items-center px-6">
        <section className="w-full rounded-3xl glass p-10 card-shadow">
          <h1 className="text-3xl font-bold text-gradient">AI Marketing Asset Engine</h1>
          <p className="mt-3 text-sm text-muted-foreground">
            Dev login is enabled. Replace this with Google OAuth in production.
          </p>
          <div className="mt-6 space-y-3">
            <input
              className="w-full rounded-xl border border-border bg-input px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email address"
            />
            <button
              onClick={loginDev}
              className="w-full rounded-xl bg-gradient-primary px-4 py-3 font-medium text-primary-foreground hover:opacity-90 transition-opacity"
            >
              Continue to Dashboard
            </button>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        </section>
      </main>
    );
  }

  return (
    <div className="min-h-screen">
      <nav className="glass border-b border-border px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-bold text-gradient">AI Marketing Engine</h1>
        <div className="flex items-center gap-4">
          {(["campaigns", "assets", "ai-studio"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setView(tab)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                view === tab
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1).replace("-", " ")}
            </button>
          ))}
          <button onClick={logout} className="text-sm text-muted-foreground hover:text-destructive transition-colors">
            Logout
          </button>
        </div>
      </nav>
      <main className="mx-auto max-w-6xl p-8">
        <div className="glass rounded-2xl p-8 card-shadow">
          <h2 className="text-2xl font-bold text-foreground capitalize">{view.replace("-", " ")}</h2>
          <p className="mt-2 text-muted-foreground">
            Connect your backend services to populate this view. See the backend/ directory for microservice APIs.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;

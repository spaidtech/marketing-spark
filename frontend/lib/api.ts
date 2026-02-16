import { config } from "./config";

function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("jwt") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse(res: Response) {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || "API request failed");
  }
  return res.json();
}

export const api = {
  me: () => fetch(`${config.authServiceUrl}/api/v1/me`, { headers: authHeaders() }).then(handleResponse),
  devToken: (email: string) =>
    fetch(`${config.authServiceUrl}/api/v1/dev-token?email=${encodeURIComponent(email)}`, {
      method: "POST",
    }).then(handleResponse),
  listCampaigns: () =>
    fetch(`${config.campaignServiceUrl}/api/v1/campaigns`, { headers: authHeaders() }).then(handleResponse),
  createCampaign: (payload: { name: string; goal: string; audience: string }) =>
    fetch(`${config.campaignServiceUrl}/api/v1/campaigns`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  listAssets: () =>
    fetch(`${config.assetServiceUrl}/api/v1/assets`, { headers: authHeaders() }).then(handleResponse),
  createAsset: (payload: any) =>
    fetch(`${config.assetServiceUrl}/api/v1/assets`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  updateAsset: (assetId: number, payload: any) =>
    fetch(`${config.assetServiceUrl}/api/v1/assets/${assetId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  generateText: (payload: any) =>
    fetch(`${config.aiServiceUrl}/api/v1/ai/generate-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  generateImage: (payload: any) =>
    fetch(`${config.aiServiceUrl}/api/v1/ai/generate-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  suggestions: (payload: any) =>
    fetch(`${config.aiServiceUrl}/api/v1/ai/suggestions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),
  balance: () =>
    fetch(`${config.billingServiceUrl}/api/v1/credits/balance`, { headers: authHeaders() }).then(handleResponse),
};


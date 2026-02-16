import { config } from "./config";

function getToken(): string | null {
  return typeof window !== "undefined" ? localStorage.getItem("jwt") : null;
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export class ApiError extends Error {
  status: number;
  body: string;

  constructor(status: number, body: string) {
    super(body || `API error ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function handleResponse(res: Response) {
  if (!res.ok) {
    const body = await res.text();
    if (res.status === 401) {
      // Clear invalid token and redirect to login
      localStorage.removeItem("jwt");
      if (typeof window !== "undefined" && window.location.pathname !== "/") {
        window.location.href = "/";
      }
    }
    throw new ApiError(res.status, body || "API request failed");
  }
  return res.json();
}

// --- Types ---

export interface Campaign {
  id: number;
  owner_id: string;
  name: string;
  goal: string;
  audience: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface AssetData {
  id: number;
  campaign_id: number;
  owner_id: string;
  asset_type: string;
  title: string;
  content: string;
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface CreditBalance {
  user_id: string;
  balance: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  credits_balance: number;
}

// --- API client ---

export const api = {
  me: (): Promise<UserProfile> =>
    fetch(`${config.authServiceUrl}/api/v1/me`, { headers: authHeaders() }).then(handleResponse),

  devToken: (email: string): Promise<{ access_token: string }> =>
    fetch(`${config.authServiceUrl}/api/v1/dev-token?email=${encodeURIComponent(email)}`, {
      method: "POST",
    }).then(handleResponse),

  listCampaigns: (page = 1, limit = 20): Promise<PaginatedResponse<Campaign>> =>
    fetch(
      `${config.campaignServiceUrl}/api/v1/campaigns?page=${page}&limit=${limit}`,
      { headers: authHeaders() },
    ).then(handleResponse),

  createCampaign: (payload: { name: string; goal: string; audience: string }): Promise<Campaign> =>
    fetch(`${config.campaignServiceUrl}/api/v1/campaigns`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  listAssets: (campaignId?: number, page = 1, limit = 20): Promise<PaginatedResponse<AssetData>> => {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (campaignId !== undefined) params.set("campaign_id", String(campaignId));
    return fetch(
      `${config.assetServiceUrl}/api/v1/assets?${params}`,
      { headers: authHeaders() },
    ).then(handleResponse);
  },

  createAsset: (payload: { campaign_id: number; asset_type: string; title: string; content?: string }): Promise<AssetData> =>
    fetch(`${config.assetServiceUrl}/api/v1/assets`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  updateAsset: (assetId: number, payload: { content: string; change_note?: string }): Promise<AssetData> =>
    fetch(`${config.assetServiceUrl}/api/v1/assets/${assetId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  generateText: (payload: { prompt: string; campaign_id?: number; tone?: string; channel?: string }) =>
    fetch(`${config.aiServiceUrl}/api/v1/ai/generate-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  generateImage: (payload: { prompt: string; campaign_id: number; style?: string; width?: number; height?: number }) =>
    fetch(`${config.aiServiceUrl}/api/v1/ai/generate-image`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  suggestions: (payload: { campaign_id: number; asset_text: string }) =>
    fetch(`${config.aiServiceUrl}/api/v1/ai/suggestions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handleResponse),

  balance: (): Promise<CreditBalance> =>
    fetch(`${config.billingServiceUrl}/api/v1/credits/balance`, { headers: authHeaders() }).then(handleResponse),
};

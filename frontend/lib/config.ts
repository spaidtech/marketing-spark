export const config = {
  authServiceUrl: process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || "http://localhost:8001",
  billingServiceUrl: process.env.NEXT_PUBLIC_BILLING_SERVICE_URL || "http://localhost:8002",
  campaignServiceUrl: process.env.NEXT_PUBLIC_CAMPAIGN_SERVICE_URL || "http://localhost:8003",
  aiServiceUrl: process.env.NEXT_PUBLIC_AI_SERVICE_URL || "http://localhost:8004",
  assetServiceUrl: process.env.NEXT_PUBLIC_ASSET_SERVICE_URL || "http://localhost:8005",
};


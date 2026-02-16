from datetime import datetime
from pydantic import BaseModel, Field

from common.models.entities import CampaignStatus


class APIMessage(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    credits_balance: int


class CampaignCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    goal: str = Field(min_length=3)
    audience: str = Field(min_length=3)


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus


class CampaignOut(CampaignCreate):
    id: int
    owner_id: str
    status: str
    created_at: datetime
    updated_at: datetime


class PaginatedCampaignOut(BaseModel):
    items: list[CampaignOut]
    total: int
    page: int
    limit: int


class AssetCreate(BaseModel):
    campaign_id: int
    asset_type: str
    title: str
    content: str = ""


class AssetUpdate(BaseModel):
    content: str
    change_note: str = "manual_edit"


class AssetOut(BaseModel):
    id: int
    campaign_id: int
    owner_id: str
    asset_type: str
    title: str
    content: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class PaginatedAssetOut(BaseModel):
    items: list[AssetOut]
    total: int
    page: int
    limit: int


class AssetVersionOut(BaseModel):
    id: int
    asset_id: int
    version_number: int
    content: str
    change_note: str
    created_at: datetime


class CreditMutation(BaseModel):
    amount: int
    reason: str
    reference_id: str = ""


class CreditBalanceOut(BaseModel):
    user_id: str
    balance: int


class LedgerEntryOut(BaseModel):
    id: int
    delta: int
    reason: str
    reference_id: str
    created_at: datetime


class PaginatedLedgerOut(BaseModel):
    items: list[LedgerEntryOut]
    total: int
    page: int
    limit: int


class AITextRequest(BaseModel):
    campaign_id: int
    prompt: str
    tone: str = "professional"
    channel: str = "landing_page"


class AIImageRequest(BaseModel):
    campaign_id: int
    prompt: str
    style: str = "modern"
    width: int = 1024
    height: int = 1024


class SuggestionRequest(BaseModel):
    campaign_id: int
    asset_text: str


class SuggestionOut(BaseModel):
    suggestions: list[str]

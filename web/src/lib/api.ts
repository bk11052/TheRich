/**
 * FastAPI 백엔드 클라이언트.
 * base URL: NEXT_PUBLIC_API_BASE (기본 http://127.0.0.1:8000)
 * 타입은 app/schemas.py 의 *Read 를 미러링.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://127.0.0.1:8000";

// ---------- enums (백엔드 app/models/base.py) ----------
export type TxnType = "expense" | "income" | "transfer";
export type TxnSource = "telegram_ocr" | "manual" | "csv" | "toss_api";
export type CategoryKind = "expense" | "income";
export type AccountType =
  | "bank"
  | "card"
  | "cash"
  | "securities"
  | "investment"
  | "real_estate"
  | "pension"
  | "loan"
  | "deposit"
  | "other";
export type AccountSide = "asset" | "liability";

// ---------- read 모델 ----------
export interface Account {
  id: number;
  name: string;
  type: AccountType;
  side: AccountSide;
  currency: string;
  balance: number;
  institution: string | null;
  is_manual: boolean;
  sort_order: number;
  archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: number;
  name: string;
  parent_id: number | null;
  kind: CategoryKind;
  icon: string | null;
  color: string | null;
  is_fixed: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: number;
  account_id: number;
  counter_account_id: number | null;
  type: TxnType;
  amount: number;
  currency: string;
  occurred_at: string;
  merchant: string | null;
  category_id: number | null;
  memo: string | null;
  source: TxnSource;
  place_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface BudgetStatus {
  budget_id: number;
  category_id: number;
  period_month: string;
  amount: number;
  spent: number;
  remaining: number;
  usage: number | null;
}

export interface AllocationSlice {
  key: string;
  label: string;
  amount: number;
}

export interface AccountBalance {
  account_id: number;
  name: string;
  type: AccountType;
  side: AccountSide;
  balance: number;
}

export interface NetWorthCurrent {
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  by_type: AllocationSlice[];
  by_account: AccountBalance[];
}

export interface NetWorthSnapshot {
  id: number;
  snapshot_date: string;
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  created_at: string;
}

// ---------- fetch 래퍼 ----------
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${path}${body ? `: ${body}` : ""}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function qs(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined);
  if (!entries.length) return "";
  return "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join("&");
}

// ---------- 엔드포인트 ----------
export const getAccounts = () => api<Account[]>("/accounts");

export const getCategories = () => api<Category[]>("/categories");

export interface CategoryInput {
  name: string;
  kind: CategoryKind;
  is_fixed?: boolean;
  parent_id?: number | null;
  icon?: string | null;
  color?: string | null;
  sort_order?: number;
}

export const createCategory = (payload: CategoryInput) =>
  api<Category>("/categories", { method: "POST", body: JSON.stringify(payload) });

export const updateCategory = (id: number, payload: Partial<CategoryInput>) =>
  api<Category>(`/categories/${id}`, { method: "PATCH", body: JSON.stringify(payload) });

export const deleteCategory = (id: number) =>
  api<void>(`/categories/${id}`, { method: "DELETE" });

// ---------- Category rules ----------
export type MatchType = "contains" | "regex" | "exact";

export interface CategoryRule {
  id: number;
  match_type: MatchType;
  pattern: string;
  category_id: number;
  priority: number;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryRuleInput {
  match_type: MatchType;
  pattern: string;
  category_id: number;
  priority?: number;
  enabled?: boolean;
}

export const getCategoryRules = () => api<CategoryRule[]>("/category-rules");

export const createCategoryRule = (payload: CategoryRuleInput) =>
  api<CategoryRule>("/category-rules", { method: "POST", body: JSON.stringify(payload) });

export const updateCategoryRule = (id: number, payload: Partial<CategoryRuleInput>) =>
  api<CategoryRule>(`/category-rules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const deleteCategoryRule = (id: number) =>
  api<void>(`/category-rules/${id}`, { method: "DELETE" });

export const getTransactions = (params: {
  month?: string;
  account_id?: number;
  category_id?: number;
  limit?: number;
  offset?: number;
} = {}) => api<Transaction[]>(`/transactions${qs(params)}`);

export interface TransactionCreate {
  account_id: number;
  type: TxnType;
  amount: number;
  currency?: string;
  occurred_at: string;
  merchant?: string | null;
  category_id?: number | null;
  memo?: string | null;
  source?: TxnSource;
}

export const createTransaction = (payload: TransactionCreate) =>
  api<Transaction>("/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export interface TransactionPatch {
  place_id?: number | null;
  memo?: string | null;
  category_id?: number | null;
  merchant?: string | null;
  amount?: number;
}

export const updateTransaction = (id: number, payload: TransactionPatch) =>
  api<Transaction>(`/transactions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const getBudgetStatus = (month: string) =>
  api<BudgetStatus[]>(`/budgets/status?month=${encodeURIComponent(month)}`);

export interface Budget {
  id: number;
  category_id: number;
  period_month: string;
  amount: number;
  created_at: string;
  updated_at: string;
}

export interface BudgetInput {
  category_id: number;
  period_month: string;
  amount: number;
}

export const getBudgets = (month: string) =>
  api<Budget[]>(`/budgets?month=${encodeURIComponent(month)}`);

export const createBudget = (payload: BudgetInput) =>
  api<Budget>("/budgets", { method: "POST", body: JSON.stringify(payload) });

export const updateBudget = (id: number, payload: Partial<BudgetInput>) =>
  api<Budget>(`/budgets/${id}`, { method: "PATCH", body: JSON.stringify(payload) });

export const deleteBudget = (id: number) =>
  api<void>(`/budgets/${id}`, { method: "DELETE" });

export const getNetWorthCurrent = () => api<NetWorthCurrent>("/net-worth/current");

export const getNetWorthSnapshots = (limit = 24) =>
  api<NetWorthSnapshot[]>(`/net-worth/snapshots?limit=${limit}`);

// ---------- Lifelog (records) ----------
export interface Tag {
  id: number;
  name: string;
  color: string | null;
}

export interface Place {
  id: number;
  name: string;
  region: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
  kakao_place_id: string | null;
  created_at: string;
}

export interface Photo {
  id: number;
  transaction_id: number | null;
  file_path: string;
  taken_at: string | null;
  created_at: string;
}

export interface RecordItem {
  id: number;
  type: TxnType;
  amount: number;
  occurred_at: string;
  merchant: string | null;
  memo: string | null;
  category_id: number | null;
  place: Place | null;
  photos: Photo[];
  tags: Tag[];
}

export const getTags = () => api<Tag[]>("/tags");

export const createTag = (payload: { name: string; color?: string | null }) =>
  api<Tag>("/tags", { method: "POST", body: JSON.stringify(payload) });

export const getRecords = (params: { tag_id?: number; month?: string } = {}) =>
  api<RecordItem[]>(`/records${qs(params)}`);

export const createPlace = (payload: {
  name: string;
  region?: string | null;
  address?: string | null;
}) => api<Place>("/places", { method: "POST", body: JSON.stringify(payload) });

export const setTransactionTags = (txnId: number, tag_ids: number[]) =>
  api<Tag[]>(`/transactions/${txnId}/tags`, {
    method: "PUT",
    body: JSON.stringify({ tag_ids }),
  });

/** 업로드된 사진의 절대 URL. file_path 는 "/uploads/<파일명>". */
export function photoUrl(filePath: string): string {
  return `${API_BASE}${filePath}`;
}

/** 사진 업로드 (multipart). api() 는 JSON 전용이라 별도 구현. */
export async function uploadPhoto(file: File, transactionId?: number): Promise<Photo> {
  const fd = new FormData();
  fd.append("file", file);
  if (transactionId != null) fd.append("transaction_id", String(transactionId));
  const res = await fetch(`${API_BASE}/photos`, { method: "POST", body: fd });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`사진 업로드 실패 ${res.status}${body ? `: ${body}` : ""}`);
  }
  return res.json() as Promise<Photo>;
}

// ---------- Cards (혜택) ----------
export type BenefitKind = "accrue" | "discount";

export interface BenefitInfo {
  id: number;
  category_id: number | null;
  category_name: string;
  kind: BenefitKind;
  rate_bp: number;
  monthly_cap: number | null;
  note: string | null;
}

export interface CardStatus {
  id: number;
  name: string;
  issuer: string | null;
  account_id: number | null;
  performance_threshold: number | null;
  annual_fee: number;
  active: boolean;
  monthly_spend: number;
  threshold_met: boolean;
  benefits: BenefitInfo[];
}

export interface BestCard {
  category_id: number | null;
  category_name: string;
  card_id: number;
  card_name: string;
  kind: BenefitKind;
  rate_bp: number;
  note: string | null;
}

export interface CardInput {
  name: string;
  issuer?: string | null;
  account_id?: number | null;
  performance_threshold?: number | null;
  annual_fee?: number;
}

export interface BenefitInput {
  category_id?: number | null;
  kind: BenefitKind;
  rate_bp: number;
  monthly_cap?: number | null;
  note?: string | null;
}

export const getCards = () => api<CardStatus[]>("/cards");
export const getBestByCategory = () => api<BestCard[]>("/cards/best-by-category");
export const createCard = (payload: CardInput) =>
  api<CardStatus>("/cards", { method: "POST", body: JSON.stringify(payload) });
export const deleteCard = (id: number) =>
  api<void>(`/cards/${id}`, { method: "DELETE" });
export const addCardBenefit = (cardId: number, payload: BenefitInput) =>
  api<BenefitInfo>(`/cards/${cardId}/benefits`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
export const deleteCardBenefit = (benefitId: number) =>
  api<void>(`/cards/benefits/${benefitId}`, { method: "DELETE" });

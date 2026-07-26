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

export const getBudgetStatus = (month: string) =>
  api<BudgetStatus[]>(`/budgets/status?month=${encodeURIComponent(month)}`);

export const getNetWorthCurrent = () => api<NetWorthCurrent>("/net-worth/current");

export const getNetWorthSnapshots = (limit = 24) =>
  api<NetWorthSnapshot[]>(`/net-worth/snapshots?limit=${limit}`);

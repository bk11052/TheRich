import {
  Banknote,
  Building2,
  CandlestickChart,
  CircleDollarSign,
  CreditCard,
  HandCoins,
  Landmark,
  PiggyBank,
  TrendingUp,
  Umbrella,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import type { AccountType } from "@/lib/api";

const ICONS: Record<AccountType, LucideIcon> = {
  bank: Landmark,
  card: CreditCard,
  cash: Wallet,
  securities: CandlestickChart,
  investment: TrendingUp,
  real_estate: Building2,
  pension: Umbrella,
  loan: HandCoins,
  deposit: PiggyBank,
  other: CircleDollarSign,
};

const LABELS: Record<AccountType, string> = {
  bank: "예금",
  card: "카드",
  cash: "현금",
  securities: "증권",
  investment: "투자",
  real_estate: "부동산",
  pension: "연금",
  loan: "대출",
  deposit: "적금",
  other: "기타",
};

export function accountIcon(type: AccountType): LucideIcon {
  return ICONS[type] ?? Banknote;
}

export function accountTypeLabel(type: AccountType): string {
  return LABELS[type] ?? type;
}

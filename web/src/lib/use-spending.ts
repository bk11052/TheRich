"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getBudgetStatus,
  getCategories,
  getTransactions,
  type BudgetStatus,
  type Category,
  type Transaction,
} from "@/lib/api";
import { dayOf, daysInMonth } from "@/lib/month";

export interface CategorySlice {
  categoryId: number | null;
  name: string;
  amount: number;
  count: number;
  colorIndex: number;
}

export interface MerchantSlice {
  merchant: string;
  amount: number;
  count: number;
  categoryId: number | null;
}

export interface SpendingData {
  loading: boolean;
  error: string | null;
  categories: Map<number, Category>;
  transactions: Transaction[];
  expenses: Transaction[];
  totalSpent: number;
  totalIncome: number;
  byCategory: CategorySlice[];
  byDay: number[]; // index 0 = day 1
  byMerchant: MerchantSlice[];
  budgets: BudgetStatus[];
  budgetTotal: number;
  budgetSpent: number;
  reload: () => void;
}

export function useSpending(month: string): SpendingData {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [budgets, setBudgets] = useState<BudgetStatus[]>([]);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      getCategories(),
      getTransactions({ month, limit: 500 }),
      getBudgetStatus(month),
    ])
      .then(([cats, txns, buds]) => {
        if (cancelled) return;
        setCategories(cats);
        setTransactions(txns);
        setBudgets(buds);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [month, reloadToken]);

  return useMemo(() => {
    const catMap = new Map(categories.map((c) => [c.id, c]));
    const expenses = transactions.filter((t) => t.type === "expense");
    const income = transactions.filter((t) => t.type === "income");

    const totalSpent = expenses.reduce((s, t) => s + t.amount, 0);
    const totalIncome = income.reduce((s, t) => s + t.amount, 0);

    // 카테고리별 집계
    const catAgg = new Map<number | null, { amount: number; count: number }>();
    for (const t of expenses) {
      const key = t.category_id ?? null;
      const cur = catAgg.get(key) ?? { amount: 0, count: 0 };
      cur.amount += t.amount;
      cur.count += 1;
      catAgg.set(key, cur);
    }
    const byCategory: CategorySlice[] = [...catAgg.entries()]
      .map(([categoryId, v]) => ({
        categoryId,
        name: categoryId != null ? (catMap.get(categoryId)?.name ?? "미분류") : "미분류",
        amount: v.amount,
        count: v.count,
        colorIndex: 0,
      }))
      .sort((a, b) => b.amount - a.amount)
      .map((s, i) => ({ ...s, colorIndex: i }));

    // 일별 집계
    const days = daysInMonth(month);
    const byDay = new Array(days).fill(0) as number[];
    for (const t of expenses) {
      const d = dayOf(t.occurred_at);
      if (d >= 1 && d <= days) byDay[d - 1] += t.amount;
    }

    // 가맹점별 집계
    const merchAgg = new Map<string, { amount: number; count: number; cat: number | null }>();
    for (const t of expenses) {
      const key = t.merchant ?? "기타";
      const cur = merchAgg.get(key) ?? { amount: 0, count: 0, cat: t.category_id ?? null };
      cur.amount += t.amount;
      cur.count += 1;
      merchAgg.set(key, cur);
    }
    const byMerchant: MerchantSlice[] = [...merchAgg.entries()]
      .map(([merchant, v]) => ({
        merchant,
        amount: v.amount,
        count: v.count,
        categoryId: v.cat,
      }))
      .sort((a, b) => b.amount - a.amount);

    const budgetTotal = budgets.reduce((s, b) => s + b.amount, 0);
    const budgetSpent = budgets.reduce((s, b) => s + b.spent, 0);

    return {
      loading,
      error,
      categories: catMap,
      transactions,
      expenses,
      totalSpent,
      totalIncome,
      byCategory,
      byDay,
      byMerchant,
      budgets,
      budgetTotal,
      budgetSpent,
      reload,
    };
  }, [categories, transactions, budgets, month, loading, error, reload]);
}

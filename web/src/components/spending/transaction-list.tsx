"use client";

import { useMemo } from "react";

import { Amount } from "@/components/amount";
import { Card } from "@/components/ui/card";
import { categoryIcon } from "@/lib/categories";
import { cn } from "@/lib/utils";
import type { Category, Transaction, TxnSource } from "@/lib/api";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];
const SOURCE_LABEL: Record<TxnSource, string> = {
  telegram_ocr: "텔레그램",
  manual: "수기",
  csv: "CSV",
  toss_api: "토스",
};

interface DayGroup {
  key: string;
  day: number;
  weekday: number;
  expense: number;
  txns: Transaction[];
}

export function TransactionList({
  transactions,
  categories,
}: {
  transactions: Transaction[];
  categories: Map<number, Category>;
}) {
  const groups = useMemo(() => {
    const map = new Map<string, DayGroup>();
    for (const t of transactions) {
      const d = new Date(t.occurred_at);
      const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      let g = map.get(key);
      if (!g) {
        g = { key, day: d.getDate(), weekday: d.getDay(), expense: 0, txns: [] };
        map.set(key, g);
      }
      if (t.type === "expense") g.expense += t.amount;
      g.txns.push(t);
    }
    return [...map.values()];
  }, [transactions]);

  if (transactions.length === 0) {
    return (
      <Card className="py-10 text-center text-sm text-muted-foreground">
        거래 내역이 없어요
      </Card>
    );
  }

  return (
    <div className="grid gap-3">
      <h2 className="px-1 text-[15px] font-semibold">거래 내역</h2>
      {groups.map((g) => (
        <Card key={g.key} className="gap-0 overflow-hidden py-0">
          <div className="flex items-center justify-between border-b bg-muted/30 px-4 py-2">
            <span className="text-[13px] font-medium">
              {g.day}일{" "}
              <span
                className={cn(
                  "text-muted-foreground",
                  g.weekday === 0 && "text-red-500/80",
                  g.weekday === 6 && "text-blue-500/80",
                )}
              >
                ({WEEKDAYS[g.weekday]})
              </span>
            </span>
            <Amount value={g.expense} compact className="text-[12px] text-muted-foreground" />
          </div>
          <ul>
            {g.txns.map((t) => {
              const cat = t.category_id != null ? categories.get(t.category_id) : undefined;
              const Icon = categoryIcon(cat?.name);
              const income = t.type === "income";
              return (
                <li
                  key={t.id}
                  className="flex items-center gap-3 border-b px-4 py-2.5 last:border-b-0"
                >
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <Icon className="size-[18px]" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {t.merchant ?? "(미상)"}
                    </p>
                    <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                      <span>{cat?.name ?? "미분류"}</span>
                      <span aria-hidden>·</span>
                      <span>{SOURCE_LABEL[t.source]}</span>
                    </p>
                  </div>
                  <Amount
                    value={income ? t.amount : -t.amount}
                    sign
                    className={cn(
                      "text-sm font-semibold",
                      income && "text-emerald-600 dark:text-emerald-400",
                    )}
                  />
                </li>
              );
            })}
          </ul>
        </Card>
      ))}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronRight, TrendingUp } from "lucide-react";

import { Amount } from "@/components/amount";
import { TransactionList } from "@/components/spending/transaction-list";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getAccounts, type Account } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import { currentMonth, monthLabel } from "@/lib/month";
import { cn } from "@/lib/utils";
import { useSpending } from "@/lib/use-spending";

function useAccounts() {
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    getAccounts()
      .then(setAccounts)
      .catch(() => setError(true));
  }, []);
  return { accounts, error };
}

export default function HomePage() {
  const month = currentMonth();
  const data = useSpending(month);
  const { accounts } = useAccounts();

  const assets =
    accounts?.filter((a) => a.side === "asset").reduce((s, a) => s + a.balance, 0) ?? 0;
  const liabilities =
    accounts?.filter((a) => a.side === "liability").reduce((s, a) => s + a.balance, 0) ?? 0;
  const netWorth = assets - liabilities;

  const usage = data.budgetTotal > 0 ? data.budgetSpent / data.budgetTotal : null;
  const over = usage != null && usage > 1;

  return (
    <div className="grid gap-4">
      <p className="px-1 text-[13px] text-muted-foreground">{monthLabel(month)}</p>

      <div className="grid gap-4 lg:grid-cols-2 lg:items-start">
        {/* 순자산 */}
        <Card className="gap-0 bg-gradient-to-br from-brand to-brand/80 p-5 text-brand-foreground">
          <div className="flex items-center gap-1.5 text-[13px] font-medium opacity-90">
            <TrendingUp className="size-4" />
            순자산
          </div>
          {accounts === null ? (
            <Skeleton className="mt-2 h-9 w-40 bg-white/25" />
          ) : (
            <Amount
              value={netWorth}
              className="mt-1 block text-[30px] font-semibold leading-none tracking-tight"
            />
          )}
          <div className="mt-4 flex gap-6 text-[12px]">
            <div>
              <p className="opacity-80">자산</p>
              <Amount value={assets} compact className="font-semibold" />
            </div>
            <div>
              <p className="opacity-80">부채</p>
              <Amount value={liabilities} compact className="font-semibold" />
            </div>
          </div>
        </Card>

        {/* 이번 달 지출 */}
        <Link href="/spending">
          <Card className="h-full gap-0 p-5 transition-colors hover:bg-accent/40">
            <div className="flex items-center justify-between">
              <p className="text-[13px] font-medium text-muted-foreground">이번 달 지출</p>
              <ChevronRight className="size-4 text-muted-foreground" />
            </div>
            {data.loading ? (
              <Skeleton className="mt-2 h-8 w-32" />
            ) : (
              <Amount
                value={data.totalSpent}
                className="mt-1 block text-[26px] font-semibold leading-none tracking-tight"
              />
            )}
            {usage != null && (
              <div className="mt-4">
                <div className="mb-1.5 flex justify-between text-[12px]">
                  <span className="text-muted-foreground">예산 소진</span>
                  <span className={cn("font-medium tabular-nums", over && "text-destructive")}>
                    {formatPercent(usage)}
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn("h-full rounded-full", over ? "bg-destructive" : "bg-brand")}
                    style={{ width: `${Math.min(usage * 100, 100)}%` }}
                  />
                </div>
              </div>
            )}
          </Card>
        </Link>

        {/* 최근 거래 */}
        {!data.loading && !data.error && (
          <div className="lg:col-span-2">
            <TransactionList
              transactions={data.transactions.slice(0, 6)}
              categories={data.categories}
            />
          </div>
        )}
      </div>
    </div>
  );
}

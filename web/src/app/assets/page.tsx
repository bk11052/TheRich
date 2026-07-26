"use client";

import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";

import { Amount } from "@/components/amount";
import { AccountList } from "@/components/assets/account-list";
import { AssetAllocation } from "@/components/assets/allocation";
import { NetWorthTrend } from "@/components/assets/networth-trend";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getNetWorthCurrent,
  getNetWorthSnapshots,
  type NetWorthCurrent,
  type NetWorthSnapshot,
} from "@/lib/api";

export default function AssetsPage() {
  const [current, setCurrent] = useState<NetWorthCurrent | null>(null);
  const [snapshots, setSnapshots] = useState<NetWorthSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getNetWorthCurrent(), getNetWorthSnapshots(24)])
      .then(([cur, snaps]) => {
        if (cancelled) return;
        setCurrent(cur);
        setSnapshots(snaps);
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
  }, []);

  if (error) {
    return (
      <Card className="grid gap-2 border-destructive/40 bg-destructive/5 p-5 text-sm">
        <p className="font-medium text-destructive">순자산 정보를 불러올 수 없어요</p>
        <p className="break-all text-[11px] text-muted-foreground/70">{error}</p>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3 lg:items-start">
      {/* 순자산 히어로 */}
      <Card className="gap-0 bg-gradient-to-br from-brand to-brand/80 p-5 text-brand-foreground lg:col-span-1">
        <div className="flex items-center gap-1.5 text-[13px] font-medium opacity-90">
          <TrendingUp className="size-4" />
          순자산
        </div>
        {loading || !current ? (
          <Skeleton className="mt-2 h-9 w-44 bg-white/25" />
        ) : (
          <>
            <Amount
              value={current.net_worth}
              className="mt-1 block text-[30px] font-semibold leading-none tracking-tight"
            />
            <div className="mt-4 flex gap-6 text-[12px]">
              <div>
                <p className="opacity-80">자산</p>
                <Amount value={current.total_assets} compact className="font-semibold" />
              </div>
              <div>
                <p className="opacity-80">부채</p>
                <Amount value={current.total_liabilities} compact className="font-semibold" />
              </div>
            </div>
          </>
        )}
      </Card>

      {loading ? (
        <>
          <Skeleton className="h-56 w-full rounded-xl lg:col-span-2" />
          <Skeleton className="h-64 w-full rounded-xl lg:col-span-1" />
          <Skeleton className="h-56 w-full rounded-xl lg:col-span-2" />
        </>
      ) : current ? (
        <>
          <div className="lg:col-span-2">
            <NetWorthTrend snapshots={snapshots} />
          </div>
          <div className="lg:col-span-1">
            <AssetAllocation slices={current.by_type} total={current.total_assets} />
          </div>
          <div className="lg:col-span-2">
            <AccountList accounts={current.by_account} />
          </div>
        </>
      ) : null}
    </div>
  );
}

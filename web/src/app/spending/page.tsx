"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { MonthNav } from "@/components/month-nav";
import { AddTransaction } from "@/components/spending/add-transaction";
import { CalendarHeatmap } from "@/components/spending/calendar-heatmap";
import { CategoryDonut } from "@/components/spending/category-donut";
import { SpendingSummary } from "@/components/spending/summary";
import { TopMerchants } from "@/components/spending/top-merchants";
import { TransactionList } from "@/components/spending/transaction-list";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { currentMonth } from "@/lib/month";
import { useSpending } from "@/lib/use-spending";

export default function SpendingPage() {
  const [month, setMonth] = useState(currentMonth);
  const [addOpen, setAddOpen] = useState(false);
  const data = useSpending(month);

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between gap-4">
        <MonthNav month={month} onChange={setMonth} className="flex-1 lg:max-w-xs" />
        {/* 데스크톱 인라인 추가 버튼 */}
        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="hidden items-center gap-1.5 rounded-full bg-brand px-4 py-2 text-sm font-semibold text-brand-foreground transition-transform active:scale-95 lg:inline-flex"
        >
          <Plus className="size-4" />
          거래 추가
        </button>
      </div>

      {data.error ? (
        <Card className="grid gap-2 border-destructive/40 bg-destructive/5 p-5 text-sm">
          <p className="font-medium text-destructive">백엔드에 연결할 수 없어요</p>
          <p className="text-muted-foreground">
            FastAPI 서버(<code className="text-xs">uvicorn app.main:app</code>)가 실행 중인지
            확인하세요.
          </p>
          <p className="break-all text-[11px] text-muted-foreground/70">{data.error}</p>
        </Card>
      ) : data.loading ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-40 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl lg:col-span-2" />
          <Skeleton className="h-56 w-full rounded-xl lg:col-span-3" />
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-12 lg:items-start">
          <div className="lg:col-span-4">
            <SpendingSummary data={data} />
          </div>
          <div className="lg:col-span-4">
            <CalendarHeatmap month={month} byDay={data.byDay} />
          </div>
          <div className="lg:col-span-4 lg:row-span-2">
            <CategoryDonut slices={data.byCategory} total={data.totalSpent} />
          </div>
          <div className="lg:col-span-8">
            <TransactionList transactions={data.transactions} categories={data.categories} />
          </div>
          <div className="lg:col-span-4">
            <TopMerchants merchants={data.byMerchant} categories={data.categories} />
          </div>
        </div>
      )}

      {/* 거래추가 FAB — 모바일 하단중앙, 데스크톱 우하단 */}
      <button
        type="button"
        onClick={() => setAddOpen(true)}
        aria-label="거래 추가"
        className="fixed bottom-24 left-1/2 z-20 flex -translate-x-1/2 items-center gap-2 rounded-full bg-brand px-5 py-3 text-sm font-semibold text-brand-foreground shadow-lg shadow-brand/30 transition-transform active:scale-95 lg:hidden"
      >
        <Plus className="size-5" />
        거래 추가
      </button>

      <AddTransaction open={addOpen} onOpenChange={setAddOpen} onCreated={data.reload} />
    </div>
  );
}

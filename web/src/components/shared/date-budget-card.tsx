"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronRight, Heart } from "lucide-react";

import { Amount } from "@/components/amount";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getSharedBudget, type SharedBudget } from "@/lib/api";
import { currentMonth } from "@/lib/month";
import { cn } from "@/lib/utils";

/** 상태별 색. warning 은 한도가 임박했다는 뜻이라 destructive 까지는 가지 않는다. */
const BAR = {
  ok: "bg-brand",
  warning: "bg-amber-500",
  over: "bg-destructive",
  unknown: "bg-muted-foreground",
} as const;

const LABEL = {
  ok: null,
  warning: "한도가 얼마 안 남았어요",
  over: "한도를 넘었어요",
  unknown: null,
} as const;

export function DateBudgetCard({ month = currentMonth() }: { month?: string }) {
  const [data, setData] = useState<SharedBudget | null | undefined>(undefined);

  useEffect(() => {
    getSharedBudget(month).then(setData);
  }, [month]);

  if (data === undefined) {
    return (
      <Card className="gap-0 p-5">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="mt-3 h-8 w-36" />
        <Skeleton className="mt-4 h-2 w-full" />
      </Card>
    );
  }

  // 아직 카테고리나 이번 달 한도를 안 잡은 상태 — 설정으로 유도한다.
  if (data === null) {
    return (
      <Link href="/more/budgets">
        <Card className="h-full gap-0 p-5 transition-colors hover:bg-accent/40">
          <div className="flex items-center justify-between">
            <p className="flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground">
              <Heart className="size-4" />
              데이트비용
            </p>
            <ChevronRight className="size-4 text-muted-foreground" />
          </div>
          <p className="mt-3 text-[13px] text-muted-foreground">
            이번 달 한도를 정하면 여기에 남은 금액이 표시돼요.
          </p>
        </Card>
      </Link>
    );
  }

  const pct = data.usage_percent ?? 0;
  const note = LABEL[data.state];

  return (
    <Link href="/spending">
      <Card className="h-full gap-0 p-5 transition-colors hover:bg-accent/40">
        <div className="flex items-center justify-between">
          <p className="flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground">
            <Heart className="size-4" />
            데이트비용
          </p>
          <ChevronRight className="size-4 text-muted-foreground" />
        </div>

        <Amount
          value={data.spent}
          className="mt-1 block text-[26px] font-semibold leading-none tracking-tight"
        />
        <p className="mt-1.5 text-[12px] text-muted-foreground">
          한도 <Amount value={data.limit} compact />
          {data.remaining >= 0 ? (
            <>
              {" · "}
              <Amount value={data.remaining} compact /> 남음
            </>
          ) : (
            <>
              {" · "}
              <span className="font-medium text-destructive">
                <Amount value={-data.remaining} compact /> 초과
              </span>
            </>
          )}
        </p>

        <div className="mt-4">
          <div className="mb-1.5 flex justify-between text-[12px]">
            <span className="text-muted-foreground">{note ?? "소진"}</span>
            <span
              className={cn(
                "font-medium tabular-nums",
                data.state === "over" && "text-destructive",
                data.state === "warning" && "text-amber-600 dark:text-amber-500",
              )}
            >
              {pct}%
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={cn("h-full rounded-full transition-[width]", BAR[data.state])}
              style={{ width: `${Math.min(pct, 100)}%` }}
            />
          </div>
        </div>
      </Card>
    </Link>
  );
}

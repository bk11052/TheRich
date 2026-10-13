"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronRight, Heart } from "lucide-react";

import { Amount } from "@/components/amount";
import { useAuth } from "@/components/providers/auth-provider";
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

/**
 * 데이트비용 한도 카드.
 * linked=false 는 데이트비용 화면 안에서 쓸 때 — 카드가 자기 화면을 가리키는 링크가 되지 않게.
 */
export function DateBudgetCard({
  month = currentMonth(),
  linked = true,
  spentWhenUnset,
}: {
  month?: string;
  linked?: boolean;
  /** 한도가 없는 달에도 월 합계는 보여주고 싶을 때(데이트비용 화면) 넘긴다. */
  spentWhenUnset?: number;
}) {
  const { status } = useAuth();
  const isOwner = status?.authenticated === true && status.role === "owner";
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

  // 아직 카테고리나 이번 달 한도를 안 잡은 상태.
  // 한도는 owner 의 예산 설정 화면에서 정하므로, partner 에게는 링크 없이 안내만 한다.
  if (data === null) {
    const body = (
      <Card className={cn("h-full gap-0 p-5", isOwner && "transition-colors hover:bg-accent/40")}>
        <div className="flex items-center justify-between">
          <p className="flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground">
            <Heart className="size-4" />
            {/* 금액을 같이 보여줄 땐 그게 한도로 읽히지 않게 제목을 지출로 */}
            {spentWhenUnset !== undefined ? "이번 달 데이트비용" : "데이트비용 한도"}
          </p>
          {isOwner && <ChevronRight className="size-4 text-muted-foreground" />}
        </div>
        {spentWhenUnset !== undefined && (
          <Amount
            value={spentWhenUnset}
            className="mt-1 block text-[26px] font-semibold leading-none tracking-tight"
          />
        )}
        <p className="mt-3 text-[13px] text-muted-foreground">
          {isOwner
            ? "예산 설정에서 이번 달 데이트 한도를 정하면 남은 금액이 표시돼요."
            : "아직 이번 달 한도가 정해지지 않았어요."}
        </p>
      </Card>
    );
    return isOwner ? <Link href="/more/budgets">{body}</Link> : body;
  }

  const pct = data.usage_percent ?? 0;
  const note = LABEL[data.state];

  const card = (
      <Card className={cn("h-full gap-0 p-5", linked && "transition-colors hover:bg-accent/40")}>
        <div className="flex items-center justify-between">
          <p className="flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground">
            <Heart className="size-4" />
            {linked ? "데이트비용" : "이번 달 데이트비용"}
          </p>
          {linked && <ChevronRight className="size-4 text-muted-foreground" />}
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
  );
  return linked ? <Link href="/shared">{card}</Link> : card;
}

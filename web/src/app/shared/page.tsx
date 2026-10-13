"use client";

import { useEffect, useMemo, useState } from "react";

import { Amount } from "@/components/amount";
import { MonthNav } from "@/components/month-nav";
import { DateBudgetCard } from "@/components/shared/date-budget-card";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  getSharedMembers,
  getSharedTransactions,
  type SharedMember,
  type SharedTransaction,
} from "@/lib/api";
import { currentMonth } from "@/lib/month";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

export default function SharedPage() {
  const [month, setMonth] = useState(currentMonth());
  const [txns, setTxns] = useState<SharedTransaction[] | null>(null);
  const [members, setMembers] = useState<SharedMember[]>([]);

  useEffect(() => {
    getSharedMembers().then(setMembers).catch(() => setMembers([]));
  }, []);

  useEffect(() => {
    setTxns(null);
    getSharedTransactions(month).then(setTxns).catch(() => setTxns([]));
  }, [month]);

  const colorOf = useMemo(() => {
    const map = new Map(members.map((m) => [m.id, m.color]));
    return (id: number | null) => (id == null ? null : map.get(id) ?? null);
  }, [members]);

  // 날짜별로 묶어 보여준다.
  const groups = useMemo(() => {
    const map = new Map<string, SharedTransaction[]>();
    for (const t of txns ?? []) {
      const d = new Date(t.occurred_at);
      const key = `${d.getMonth() + 1}-${d.getDate()}-${d.getDay()}`;
      const bucket = map.get(key);
      if (bucket) {
        bucket.push(t);
      } else {
        map.set(key, [t]);
      }
    }
    return [...map.entries()];
  }, [txns]);

  return (
    <div className="grid gap-4">
      <MonthNav month={month} onChange={setMonth} />

      <DateBudgetCard month={month} />

      {txns === null ? (
        <Skeleton className="h-32 w-full" />
      ) : txns.length === 0 ? (
        <Card className="p-6">
          <p className="text-center text-[13px] text-muted-foreground">
            이 달에 기록된 데이트비용이 없어요.
            <br />
            텔레그램 봇에 &quot;가맹점 금액&quot;으로 보내면 여기에 쌓여요.
          </p>
        </Card>
      ) : (
        <div className="grid gap-3">
          <p className="px-1 text-[13px] font-medium text-muted-foreground">내역</p>
          {groups.map(([key, rows]) => {
            const [m, d, wd] = key.split("-").map(Number);
            return (
              <Card key={key} className="gap-0 overflow-hidden p-0">
                <div className="flex items-center justify-between border-b px-4 py-2 text-[12px] text-muted-foreground">
                  <span>
                    {m}월 {d}일 ({WEEKDAYS[wd]})
                  </span>
                  <Amount value={rows.reduce((s, t) => s + t.amount, 0)} compact />
                </div>
                <ul>
                  {rows.map((t) => {
                    const color = colorOf(t.payer_id);
                    return (
                      <li
                        key={t.id}
                        className="flex items-center gap-3 border-b px-4 py-2.5 last:border-b-0"
                      >
                        <span
                          aria-hidden
                          className="size-2.5 shrink-0 rounded-full ring-1 ring-black/10"
                          style={{
                            backgroundColor: color ?? "var(--muted-foreground)",
                          }}
                        />
                        <p className="min-w-0 flex-1 truncate text-sm font-medium">
                          {t.merchant ?? "(미상)"}
                        </p>
                        <Amount value={-t.amount} sign className="text-sm font-semibold" />
                      </li>
                    );
                  })}
                </ul>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

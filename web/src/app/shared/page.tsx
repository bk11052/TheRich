"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";

import { Amount } from "@/components/amount";
import { MonthNav } from "@/components/month-nav";
import { DateBudgetCard } from "@/components/shared/date-budget-card";
import { CalendarHeatmap } from "@/components/spending/calendar-heatmap";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getSharedTransactions, type SharedTransaction } from "@/lib/api";
import { currentMonth, daysInMonth, parseMonth } from "@/lib/month";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

/**
 * 데이트비용 탭. owner 와 partner 가 똑같은 화면을 본다.
 * 한도 카드 → 일별 합계 달력 → (날짜를 누르면) 그날 내역 / (안 누르면) 달 전체 내역.
 * 사람 구분·수입은 없다.
 */
export default function SharedPage() {
  const [month, setMonth] = useState(currentMonth());
  const [txns, setTxns] = useState<SharedTransaction[] | null>(null);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  useEffect(() => {
    setTxns(null);
    setSelectedDay(null); // 다른 달로 가면 선택한 날은 의미가 없다
    getSharedTransactions(month)
      .then(setTxns)
      .catch(() => setTxns([]));
  }, [month]);

  const byDay = useMemo(() => {
    const out = Array<number>(daysInMonth(month)).fill(0);
    for (const t of txns ?? []) out[new Date(t.occurred_at).getDate() - 1] += t.amount;
    return out;
  }, [txns, month]);

  const monthTotal = useMemo(() => byDay.reduce((a, b) => a + b, 0), [byDay]);

  // 날짜별 묶음 (최신 날짜 먼저). 날짜를 골랐으면 그날만.
  const groups = useMemo(() => {
    const map = new Map<number, SharedTransaction[]>();
    for (const t of txns ?? []) {
      const d = new Date(t.occurred_at).getDate();
      if (selectedDay !== null && d !== selectedDay) continue;
      const bucket = map.get(d);
      if (bucket) bucket.push(t);
      else map.set(d, [t]);
    }
    return [...map.entries()].sort((a, b) => b[0] - a[0]);
  }, [txns, selectedDay]);

  const { year, month: m } = parseMonth(month);
  const weekdayOf = (d: number) => WEEKDAYS[new Date(year, m - 1, d).getDay()];

  return (
    <div className="grid gap-4">
      <MonthNav month={month} onChange={setMonth} />

      {/* 월 합계는 한도 카드가 맡는다(한도가 없어도 합계는 보이게). 달력엔 일별만. */}
      <DateBudgetCard month={month} linked={false} spentWhenUnset={monthTotal} />

      {/* 지출 탭과 같은 달력. 칸은 칠하지 않고 금액 글자 색으로 적음~많음을 보여준다. */}
      {txns === null ? (
        <Skeleton className="h-96 w-full rounded-xl" />
      ) : (
        <CalendarHeatmap
          month={month}
          byDay={byDay}
          variant="text"
          selectedDay={selectedDay}
          onSelect={setSelectedDay}
        />
      )}

      <div className="grid gap-3">
        <div className="flex items-center justify-between px-1">
          <p className="text-[13px] font-medium text-muted-foreground">
            {selectedDay === null
              ? "이번 달 내역"
              : `${m}월 ${selectedDay}일 (${weekdayOf(selectedDay)})`}
          </p>
          {selectedDay !== null && (
            <button
              type="button"
              onClick={() => setSelectedDay(null)}
              className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              <X className="size-3.5" />
              전체 보기
            </button>
          )}
        </div>

        {txns === null ? (
          <Skeleton className="h-24 w-full" />
        ) : groups.length === 0 ? (
          <Card className="p-6">
            <p className="text-center text-[13px] text-muted-foreground">
              {selectedDay === null ? (
                <>
                  이 달에 기록된 데이트비용이 없어요.
                  <br />
                  텔레그램 봇에 &quot;가맹점 금액&quot;으로 보내면 여기에 쌓여요.
                </>
              ) : (
                "이 날은 지출이 없어요."
              )}
            </p>
          </Card>
        ) : (
          groups.map(([day, rows]) => (
            <Card key={day} className="gap-0 overflow-hidden p-0">
              <div className="flex items-center justify-between border-b px-4 py-2 text-[12px] text-muted-foreground">
                {/* 날짜를 골랐으면 위 제목이 이미 날짜이므로 여기는 합계만 */}
                <span>{selectedDay === null ? `${m}월 ${day}일 (${weekdayOf(day)})` : "합계"}</span>
                <Amount value={rows.reduce((s, t) => s + t.amount, 0)} compact />
              </div>
              <ul>
                {rows.map((t) => (
                  <li
                    key={t.id}
                    className="flex items-center gap-3 border-b px-4 py-3 last:border-b-0"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{t.merchant ?? "(미상)"}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {new Date(t.occurred_at).toLocaleTimeString("ko-KR", {
                          hour: "numeric",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                    <Amount value={-t.amount} className="text-sm font-semibold" />
                  </li>
                ))}
              </ul>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

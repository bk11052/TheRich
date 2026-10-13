"use client";

import { daysInMonth, firstWeekday, parseMonth } from "@/lib/month";
import { cn } from "@/lib/utils";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

/** 칸이 좁으므로 100만 원 이상은 만 단위로 줄인다: 1,250,000 → -125만 */
function dayAmount(n: number): string {
  if (n >= 1_000_000) return `-${Math.round(n / 10_000).toLocaleString("ko-KR")}만`;
  return `-${n.toLocaleString("ko-KR")}`;
}

/**
 * 일별 데이트비용 달력. 칸마다 그날의 지출 합계를 적고, 누르면 그날을 고른다.
 * 사람 구분이 없으므로 금액은 모두 같은 색. 수입은 다루지 않는다.
 */
export function DateCalendar({
  month,
  byDay,
  selectedDay,
  onSelect,
}: {
  month: string;
  /** byDay[d-1] = d일 지출 합계 */
  byDay: number[];
  selectedDay: number | null;
  onSelect: (day: number | null) => void;
}) {
  const days = daysInMonth(month);
  const lead = firstWeekday(month);
  const { year, month: m } = parseMonth(month);

  const now = new Date();
  const isThisMonth = now.getFullYear() === year && now.getMonth() + 1 === m;
  const today = isThisMonth ? now.getDate() : null;

  const cells: (number | null)[] = [
    ...Array(lead).fill(null),
    ...Array.from({ length: days }, (_, i) => i + 1),
  ];

  return (
    <div>
      <div className="grid grid-cols-7">
        {WEEKDAYS.map((w) => (
          <div key={w} className="pb-2 text-center text-[12px] text-muted-foreground">
            {w}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-y-1">
        {cells.map((day, idx) => {
          if (day === null) return <div key={`e-${idx}`} />;
          const amount = byDay[day - 1] ?? 0;
          const selected = selectedDay === day;
          const isToday = today === day;
          return (
            <button
              key={day}
              type="button"
              // 같은 날을 다시 누르면 선택 해제 → 다시 달 전체 내역
              onClick={() => onSelect(selected ? null : day)}
              aria-pressed={selected}
              aria-label={`${m}월 ${day}일${amount > 0 ? ` 지출 ${amount.toLocaleString("ko-KR")}원` : " 지출 없음"}`}
              className="flex min-h-[54px] flex-col items-center rounded-lg pt-1 transition-colors hover:bg-accent/60"
            >
              <span
                className={cn(
                  "flex size-7 items-center justify-center rounded-full text-[15px] tabular-nums",
                  selected
                    ? "bg-brand font-semibold text-brand-foreground"
                    : isToday
                      ? "bg-brand/15 font-semibold text-foreground"
                      : amount > 0
                        ? "text-foreground"
                        : "text-muted-foreground/60",
                )}
              >
                {day}
              </span>
              {amount > 0 && (
                <span
                  data-private=""
                  className="mt-0.5 max-w-full truncate px-0.5 text-[10.5px] leading-tight tracking-tight text-muted-foreground tabular-nums"
                >
                  {dayAmount(amount)}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

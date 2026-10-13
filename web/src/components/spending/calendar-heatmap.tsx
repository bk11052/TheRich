"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatKRW } from "@/lib/format";
import { daysInMonth, firstWeekday, parseMonth } from "@/lib/month";
import { cn } from "@/lib/utils";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function intensity(amount: number, max: number): number {
  if (amount <= 0 || max <= 0) return 0;
  const r = amount / max;
  if (r > 0.75) return 4;
  if (r > 0.5) return 3;
  if (r > 0.25) return 2;
  return 1;
}

// fill: 칸 배경 농도. 0 은 투명.
const LEVEL_ALPHA = ["0%", "18%", "38%", "62%", "90%"];

// text: 금액 글자 색. 단계별 색은 globals.css 의 --heat-1..4 (테마마다 다름).
const textColor = (level: number) => `var(--heat-${Math.max(1, level)})`;

/**
 * 칸에 적는 금액. 이 달력엔 지출만 오므로 '-' 부호는 구분해주는 게 없고 폭만 먹는다
 * (6자리 금액 + 부호면 옆 칸 숫자와 붙어 보였다). 100만 원 이상은 만 단위로: 1,250,000 → 125만
 */
function dayAmount(n: number): string {
  if (n >= 1_000_000) return `${Math.round(n / 10_000).toLocaleString("ko-KR")}만`;
  return n.toLocaleString("ko-KR");
}

/**
 * 일별 지출 달력. 지출 탭과 데이트비용 탭이 함께 쓴다.
 *
 * - variant="fill" (지출 탭): 칸 배경을 지출 농도로 칠한다.
 * - variant="text" (데이트비용 탭): 칸은 칠하지 않고, 칸에 적은 금액의 글자 색으로 농도를 보여준다.
 *   onSelect 를 주면 날짜를 눌러 고를 수 있다(같은 날을 다시 누르면 해제).
 */
export function CalendarHeatmap({
  month,
  byDay,
  variant = "fill",
  selectedDay = null,
  onSelect,
}: {
  month: string;
  /** byDay[d-1] = d일 지출 합계 */
  byDay: number[];
  variant?: "fill" | "text";
  selectedDay?: number | null;
  onSelect?: (day: number | null) => void;
}) {
  const days = daysInMonth(month);
  const lead = firstWeekday(month);
  const max = Math.max(0, ...byDay);
  const cells: (number | null)[] = [
    ...Array(lead).fill(null),
    ...Array.from({ length: days }, (_, i) => i + 1),
  ];

  const { year, month: m } = parseMonth(month);
  const now = new Date();
  const today =
    now.getFullYear() === year && now.getMonth() + 1 === m ? now.getDate() : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[15px]">일별 지출</CardTitle>
      </CardHeader>
      {/* text 변형은 칸에 금액을 적어야 하므로 좌우 여백을 줄여 칸 폭을 확보한다 */}
      <CardContent className={cn(variant === "text" && "px-2")}>
        <div className={cn("grid grid-cols-7", variant === "fill" ? "gap-1.5" : "gap-x-0.5 gap-y-1")}>
          {WEEKDAYS.map((w, i) => (
            <div
              key={w}
              className={cn(
                "pb-1 text-center text-[11px] font-medium text-muted-foreground",
                i === 0 && "text-red-500/70",
                i === 6 && "text-blue-500/70",
              )}
            >
              {w}
            </div>
          ))}
          {cells.map((day, idx) => {
            if (day === null) return <div key={`e-${idx}`} />;
            const amount = byDay[day - 1] ?? 0;
            const level = intensity(amount, max);

            if (variant === "text") {
              const selected = selectedDay === day;
              const isToday = today === day;
              return (
                <button
                  key={day}
                  type="button"
                  onClick={onSelect ? () => onSelect(selected ? null : day) : undefined}
                  disabled={!onSelect}
                  aria-pressed={onSelect ? selected : undefined}
                  aria-label={`${m}월 ${day}일${amount > 0 ? ` 지출 ${amount.toLocaleString("ko-KR")}원` : " 지출 없음"}`}
                  className="flex min-h-[54px] flex-col items-center rounded-lg pt-1 transition-colors enabled:hover:bg-accent/60"
                >
                  <span
                    className={cn(
                      "flex size-7 items-center justify-center rounded-full text-[14px] tabular-nums",
                      selected
                        ? "bg-brand font-semibold text-brand-foreground"
                        : isToday
                          ? "font-semibold text-foreground ring-1 ring-brand/60"
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
                      className={cn(
                        "mt-0.5 max-w-full truncate text-[10px] leading-tight tracking-[-0.03em] tabular-nums",
                        level === 4 && "font-semibold",
                      )}
                      style={{ color: textColor(level) }}
                    >
                      {dayAmount(amount)}
                    </span>
                  )}
                </button>
              );
            }

            return (
              <div
                key={day}
                title={amount > 0 ? `${month}-${String(day).padStart(2, "0")} · ${formatKRW(amount)}` : undefined}
                className={cn(
                  "flex aspect-square flex-col items-center justify-center rounded-lg border text-[11px] tabular-nums",
                  level === 0 ? "border-transparent bg-muted/50 text-muted-foreground" : "border-transparent text-foreground",
                )}
                style={
                  level > 0
                    ? {
                        backgroundColor: `color-mix(in oklch, var(--brand) ${LEVEL_ALPHA[level]}, transparent)`,
                      }
                    : undefined
                }
              >
                {day}
              </div>
            );
          })}
        </div>

        {/* 범례는 칸을 칠하는 지출 탭에만. 데이트비용(text)은 금액 글자 색이 그 자체로 읽힌다. */}
        {variant === "fill" && (
          <div className="mt-3 flex items-center justify-end gap-1.5 text-[10px] text-muted-foreground">
            <span>적음</span>
            {LEVEL_ALPHA.map((a, i) => (
              <span
                key={i}
                className="size-3 rounded-[4px] border"
                style={{ backgroundColor: `color-mix(in oklch, var(--brand) ${a}, transparent)` }}
              />
            ))}
            <span>많음</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

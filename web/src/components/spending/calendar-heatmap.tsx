"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatKRW } from "@/lib/format";
import { daysInMonth, firstWeekday } from "@/lib/month";
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

const LEVEL_ALPHA = ["0%", "18%", "38%", "62%", "90%"];

export function CalendarHeatmap({
  month,
  byDay,
}: {
  month: string;
  byDay: number[];
}) {
  const days = daysInMonth(month);
  const lead = firstWeekday(month);
  const max = Math.max(0, ...byDay);
  const cells: (number | null)[] = [
    ...Array(lead).fill(null),
    ...Array.from({ length: days }, (_, i) => i + 1),
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[15px]">일별 지출</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 gap-1.5">
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

        {/* 범례 */}
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
      </CardContent>
    </Card>
  );
}

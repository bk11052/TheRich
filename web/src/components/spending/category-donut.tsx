"use client";

import { useMemo } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

import { Amount } from "@/components/amount";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { categoryIcon, chartColor } from "@/lib/categories";
import { formatPercent } from "@/lib/format";
import type { CategorySlice } from "@/lib/use-spending";

const MAX_SLICES = 7;

export function CategoryDonut({
  slices,
  total,
}: {
  slices: CategorySlice[];
  total: number;
}) {
  const display = useMemo(() => {
    if (slices.length <= MAX_SLICES) return slices;
    const head = slices.slice(0, MAX_SLICES);
    const restAmount = slices
      .slice(MAX_SLICES)
      .reduce((s, x) => s + x.amount, 0);
    return [
      ...head,
      {
        categoryId: null,
        name: "기타",
        amount: restAmount,
        count: 0,
        colorIndex: MAX_SLICES,
      } as CategorySlice,
    ];
  }, [slices]);

  if (total <= 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-[15px]">카테고리별 지출</CardTitle>
        </CardHeader>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          이 달 지출 내역이 없어요
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[15px]">카테고리별 지출</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-5">
        {/* 도넛 */}
        <div className="relative mx-auto h-44 w-44">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={display}
                dataKey="amount"
                nameKey="name"
                innerRadius={62}
                outerRadius={86}
                paddingAngle={2}
                strokeWidth={0}
                startAngle={90}
                endAngle={-270}
              >
                {display.map((s) => (
                  <Cell key={s.name} fill={chartColor(s.colorIndex)} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-[11px] text-muted-foreground">총 지출</span>
            <Amount
              value={total}
              compact
              className="text-lg font-semibold tracking-tight"
            />
          </div>
        </div>

        {/* 범례 리스트 */}
        <ul className="grid gap-1">
          {display.map((s) => {
            const Icon = categoryIcon(s.name);
            const pct = s.amount / total;
            return (
              <li key={s.name} className="flex items-center gap-3 py-1.5">
                <span
                  className="flex size-8 shrink-0 items-center justify-center rounded-full"
                  style={{
                    backgroundColor: `color-mix(in oklch, ${chartColor(
                      s.colorIndex,
                    )} 16%, transparent)`,
                    color: chartColor(s.colorIndex),
                  }}
                >
                  <Icon className="size-[17px]" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="truncate text-sm font-medium">{s.name}</span>
                    <Amount value={s.amount} compact className="text-sm font-semibold" />
                  </div>
                  <span className="text-[11px] text-muted-foreground">
                    {formatPercent(pct)}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}

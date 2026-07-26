"use client";

import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

import { Amount } from "@/components/amount";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { chartColor } from "@/lib/categories";
import { accountIcon } from "@/lib/accounts";
import { formatPercent } from "@/lib/format";
import type { AllocationSlice, AccountType } from "@/lib/api";

export function AssetAllocation({
  slices,
  total,
}: {
  slices: AllocationSlice[];
  total: number;
}) {
  if (total <= 0 || slices.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[15px]">자산 배분</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-5">
        <div className="relative mx-auto h-40 w-40">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={slices}
                dataKey="amount"
                nameKey="label"
                innerRadius={56}
                outerRadius={78}
                paddingAngle={2}
                strokeWidth={0}
                startAngle={90}
                endAngle={-270}
              >
                {slices.map((s, i) => (
                  <Cell key={s.key} fill={chartColor(i)} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-[11px] text-muted-foreground">총 자산</span>
            <Amount value={total} compact className="text-lg font-semibold tracking-tight" />
          </div>
        </div>

        <ul className="grid gap-1">
          {slices.map((s, i) => {
            const Icon = accountIcon(s.key as AccountType);
            return (
              <li key={s.key} className="flex items-center gap-3 py-1.5">
                <span
                  className="flex size-8 shrink-0 items-center justify-center rounded-full"
                  style={{
                    backgroundColor: `color-mix(in oklch, ${chartColor(i)} 16%, transparent)`,
                    color: chartColor(i),
                  }}
                >
                  <Icon className="size-[17px]" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="truncate text-sm font-medium">{s.label}</span>
                    <Amount value={s.amount} compact className="text-sm font-semibold" />
                  </div>
                  <span className="text-[11px] text-muted-foreground">
                    {formatPercent(s.amount / total)}
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

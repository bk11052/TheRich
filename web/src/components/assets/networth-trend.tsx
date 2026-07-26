"use client";

import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Amount } from "@/components/amount";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatKRW, formatManwon } from "@/lib/format";
import type { NetWorthSnapshot } from "@/lib/api";

function monthTick(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}월`;
}

interface TooltipProps {
  active?: boolean;
  payload?: { value: number; payload: NetWorthSnapshot }[];
}

function ChartTooltip({ active, payload }: TooltipProps) {
  if (!active || !payload?.length) return null;
  const snap = payload[0].payload;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="mb-0.5 text-muted-foreground">{snap.snapshot_date}</p>
      <p className="font-semibold tabular-nums">{formatKRW(snap.net_worth)}</p>
    </div>
  );
}

export function NetWorthTrend({ snapshots }: { snapshots: NetWorthSnapshot[] }) {
  if (snapshots.length < 2) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[15px]">순자산 추이</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-40 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={snapshots} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
              <defs>
                <linearGradient id="nw-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--brand)" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="var(--brand)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="snapshot_date"
                tickFormatter={monthTick}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                minTickGap={16}
              />
              <YAxis
                width={40}
                tickFormatter={(v: number) => formatManwon(v)}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 10, fill: "var(--muted-foreground)" }}
                domain={["dataMin - 300000", "dataMax + 300000"]}
              />
              <Tooltip content={<ChartTooltip />} cursor={{ stroke: "var(--border)" }} />
              <Area
                type="monotone"
                dataKey="net_worth"
                stroke="var(--brand)"
                strokeWidth={2.5}
                fill="url(#nw-fill)"
                dot={{ r: 2.5, fill: "var(--brand)", strokeWidth: 0 }}
                activeDot={{ r: 4 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
          <span>최근 {snapshots.length}개 스냅샷</span>
          <span className="flex items-center gap-1">
            기간 변화
            <Amount
              value={snapshots[snapshots.length - 1].net_worth - snapshots[0].net_worth}
              compact
              sign
              className="font-semibold text-emerald-600 dark:text-emerald-400"
            />
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

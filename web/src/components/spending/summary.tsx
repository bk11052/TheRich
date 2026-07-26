import { Amount } from "@/components/amount";
import { Card } from "@/components/ui/card";
import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { SpendingData } from "@/lib/use-spending";

export function SpendingSummary({ data }: { data: SpendingData }) {
  const { totalSpent, totalIncome, budgetTotal, budgetSpent } = data;
  const usage = budgetTotal > 0 ? budgetSpent / budgetTotal : null;
  const over = usage != null && usage > 1;
  const net = totalIncome - totalSpent;

  return (
    <Card className="gap-0 overflow-hidden p-0">
      <div className="p-5">
        <p className="text-[13px] font-medium text-muted-foreground">이번 달 지출</p>
        <Amount
          value={totalSpent}
          className="mt-1 block text-[32px] font-semibold leading-none tracking-tight"
        />

        {usage != null && (
          <div className="mt-4">
            <div className="mb-1.5 flex items-center justify-between text-[12px]">
              <span className="text-muted-foreground">예산</span>
              <span className={cn("font-medium tabular-nums", over && "text-destructive")}>
                {formatPercent(usage)}
                <span className="text-muted-foreground"> 소진</span>
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  over ? "bg-destructive" : "bg-brand",
                )}
                style={{ width: `${Math.min((usage ?? 0) * 100, 100)}%` }}
              />
            </div>
            <div className="mt-1.5 flex justify-between text-[11px] text-muted-foreground">
              <Amount value={budgetSpent} compact />
              <Amount value={budgetTotal} compact />
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 border-t">
        <div className="border-r px-5 py-3">
          <p className="text-[12px] text-muted-foreground">수입</p>
          <Amount value={totalIncome} compact className="text-[15px] font-semibold" />
        </div>
        <div className="px-5 py-3">
          <p className="text-[12px] text-muted-foreground">순액</p>
          <Amount
            value={net}
            compact
            sign
            className={cn(
              "text-[15px] font-semibold",
              net >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-destructive",
            )}
          />
        </div>
      </div>
    </Card>
  );
}

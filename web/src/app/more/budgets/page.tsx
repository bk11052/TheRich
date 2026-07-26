"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Amount } from "@/components/amount";
import { ManageHeader } from "@/components/manage/page-header";
import { MonthNav } from "@/components/month-nav";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  createBudget,
  deleteBudget,
  getBudgets,
  updateBudget,
  type Budget,
  type Category,
} from "@/lib/api";
import { categoryIcon } from "@/lib/categories";
import { formatManwon, formatPercent } from "@/lib/format";
import { currentMonth } from "@/lib/month";
import { cn } from "@/lib/utils";
import { useSpending } from "@/lib/use-spending";

export default function BudgetsPage() {
  const [month, setMonth] = useState(currentMonth);
  const spending = useSpending(month);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [budgetsLoading, setBudgetsLoading] = useState(true);

  const reloadBudgets = useCallback(() => {
    setBudgetsLoading(true);
    getBudgets(month)
      .then(setBudgets)
      .catch(() => toast.error("예산을 불러오지 못했어요"))
      .finally(() => setBudgetsLoading(false));
  }, [month]);

  useEffect(reloadBudgets, [reloadBudgets]);

  const expenseCategories = useMemo(
    () =>
      [...spending.categories.values()]
        .filter((c) => c.kind === "expense")
        .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id),
    [spending.categories],
  );

  const spentByCat = useMemo(() => {
    const m = new Map<number, number>();
    for (const s of spending.byCategory) {
      if (s.categoryId != null) m.set(s.categoryId, s.amount);
    }
    return m;
  }, [spending.byCategory]);

  const budgetByCat = useMemo(
    () => new Map(budgets.map((b) => [b.category_id, b])),
    [budgets],
  );

  const totalBudget = budgets.reduce((s, b) => s + b.amount, 0);
  const loading = spending.loading || budgetsLoading;

  return (
    <div className="mx-auto w-full max-w-xl">
      <ManageHeader title="예산 설정" />
      <MonthNav month={month} onChange={setMonth} className="mb-4" />

      {/* 요약 */}
      <Card className="mb-4 grid grid-cols-2 gap-0 p-0">
        <div className="border-r px-5 py-3">
          <p className="text-[12px] text-muted-foreground">총 예산</p>
          <Amount value={totalBudget} compact className="text-[17px] font-semibold" />
        </div>
        <div className="px-5 py-3">
          <p className="text-[12px] text-muted-foreground">이번 달 지출</p>
          <Amount
            value={spending.totalSpent}
            compact
            className="text-[17px] font-semibold"
          />
        </div>
      </Card>

      {loading ? (
        <div className="grid gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <Card className="gap-0 overflow-hidden py-0">
          {expenseCategories.map((cat) => (
            <BudgetRow
              key={cat.id}
              category={cat}
              spent={spentByCat.get(cat.id) ?? 0}
              budget={budgetByCat.get(cat.id)}
              month={month}
              onChanged={reloadBudgets}
            />
          ))}
        </Card>
      )}
      <p className="mt-3 px-1 text-[11px] text-muted-foreground/70">
        금액을 입력하고 Enter 또는 포커스를 벗어나면 저장돼요. 0으로 지우면 예산이 삭제됩니다.
      </p>
    </div>
  );
}

function BudgetRow({
  category,
  spent,
  budget,
  month,
  onChanged,
}: {
  category: Category;
  spent: number;
  budget?: Budget;
  month: string;
  onChanged: () => void;
}) {
  const Icon = categoryIcon(category.name);
  const [value, setValue] = useState(budget ? String(budget.amount) : "");
  const [saving, setSaving] = useState(false);

  // 외부(월 변경 등)로 budget 바뀌면 입력값 동기화
  useEffect(() => {
    setValue(budget ? String(budget.amount) : "");
  }, [budget]);

  const amount = budget?.amount ?? 0;
  const usage = amount > 0 ? spent / amount : null;
  const over = usage != null && usage > 1;

  async function save() {
    const next = Math.round(Number(value)) || 0;
    const prev = budget?.amount ?? 0;
    if (next === prev) return;
    setSaving(true);
    try {
      if (next <= 0 && budget) {
        await deleteBudget(budget.id);
        toast.success(`${category.name} 예산 삭제`);
      } else if (budget) {
        await updateBudget(budget.id, { amount: next });
        toast.success(`${category.name} 예산 저장`);
      } else if (next > 0) {
        await createBudget({
          category_id: category.id,
          period_month: month,
          amount: next,
        });
        toast.success(`${category.name} 예산 저장`);
      }
      onChanged();
    } catch (e) {
      toast.error("저장 실패", {
        description: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="border-b px-4 py-3 last:border-b-0">
      <div className="flex items-center gap-3">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <Icon className="size-[16px]" />
        </span>
        <span className="flex-1 text-sm font-medium">{category.name}</span>
        <div className="flex items-center gap-1">
          <Input
            type="number"
            inputMode="numeric"
            placeholder="예산 없음"
            value={value}
            disabled={saving}
            onChange={(e) => setValue(e.target.value)}
            onBlur={save}
            onKeyDown={(e) => {
              if (e.key === "Enter") e.currentTarget.blur();
            }}
            className="h-8 w-28 text-right text-sm tabular-nums"
          />
          <span className="w-5 text-[11px] text-muted-foreground">원</span>
        </div>
      </div>

      {/* 소진율 */}
      <div className="mt-2 flex items-center gap-2 pl-11">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
          {usage != null && (
            <div
              className={cn("h-full rounded-full", over ? "bg-destructive" : "bg-brand")}
              style={{ width: `${Math.min(usage * 100, 100)}%` }}
            />
          )}
        </div>
        <span className="shrink-0 text-[11px] tabular-nums text-muted-foreground">
          {formatManwon(spent)}
          {usage != null && (
            <span className={cn("ml-1", over && "text-destructive")}>
              ({formatPercent(usage)})
            </span>
          )}
        </span>
      </div>
    </div>
  );
}

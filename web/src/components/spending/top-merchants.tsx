import { Amount } from "@/components/amount";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { categoryIcon } from "@/lib/categories";
import type { MerchantSlice } from "@/lib/use-spending";
import type { Category } from "@/lib/api";

export function TopMerchants({
  merchants,
  categories,
  limit = 5,
}: {
  merchants: MerchantSlice[];
  categories: Map<number, Category>;
  limit?: number;
}) {
  const top = merchants.slice(0, limit);
  if (top.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-[15px]">상위 지출처</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-0.5">
        {top.map((m, i) => {
          const catName = m.categoryId != null ? categories.get(m.categoryId)?.name : undefined;
          const Icon = categoryIcon(catName);
          return (
            <div key={m.merchant} className="flex items-center gap-3 py-2">
              <span className="w-4 text-center text-[13px] font-semibold text-muted-foreground tabular-nums">
                {i + 1}
              </span>
              <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <Icon className="size-[16px]" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{m.merchant}</p>
                <p className="text-[11px] text-muted-foreground">{m.count}건</p>
              </div>
              <Amount value={m.amount} compact className="text-sm font-semibold" />
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

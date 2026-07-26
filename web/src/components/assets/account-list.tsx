import { Amount } from "@/components/amount";
import { Card } from "@/components/ui/card";
import { accountIcon, accountTypeLabel } from "@/lib/accounts";
import { cn } from "@/lib/utils";
import type { AccountBalance } from "@/lib/api";

function Section({ title, accounts }: { title: string; accounts: AccountBalance[] }) {
  if (accounts.length === 0) return null;
  const total = accounts.reduce((s, a) => s + a.balance, 0);
  return (
    <div className="grid gap-2">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-[13px] font-medium text-muted-foreground">{title}</h2>
        <Amount value={total} compact className="text-[12px] font-medium text-muted-foreground" />
      </div>
      <Card className="gap-0 overflow-hidden py-0">
        {accounts.map((a) => {
          const Icon = accountIcon(a.type);
          return (
            <div
              key={a.account_id}
              className="flex items-center gap-3 border-b px-4 py-3 last:border-b-0"
            >
              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <Icon className="size-[18px]" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{a.name}</p>
                <p className="text-[11px] text-muted-foreground">{accountTypeLabel(a.type)}</p>
              </div>
              <Amount
                value={a.balance}
                compact
                className={cn(
                  "text-sm font-semibold",
                  a.side === "liability" && "text-destructive",
                )}
              />
            </div>
          );
        })}
      </Card>
    </div>
  );
}

export function AccountList({ accounts }: { accounts: AccountBalance[] }) {
  const assets = accounts.filter((a) => a.side === "asset");
  const liabilities = accounts.filter((a) => a.side === "liability");
  return (
    <div className="grid gap-5">
      <Section title="자산" accounts={assets} />
      <Section title="부채" accounts={liabilities} />
    </div>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CreditCard, Plus, Trash2, TrendingUp } from "lucide-react";
import { toast } from "sonner";

import { Amount } from "@/components/amount";
import { ManageHeader } from "@/components/manage/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  addCardBenefit,
  createCard,
  deleteCard,
  deleteCardBenefit,
  getAccounts,
  getBestByCategory,
  getCards,
  getCategories,
  type Account,
  type BenefitInfo,
  type BenefitKind,
  type BestCard,
  type CardStatus,
  type Category,
} from "@/lib/api";
import { formatManwon, formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";

function kindLabel(k: BenefitKind) {
  return k === "discount" ? "할인" : "적립";
}
function ratePct(bp: number) {
  return `${(bp / 100).toFixed(bp % 100 ? 1 : 0)}%`;
}

export default function CardsPage() {
  const [cards, setCards] = useState<CardStatus[]>([]);
  const [best, setBest] = useState<BestCard[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [cardOpen, setCardOpen] = useState(false);
  const [benefitFor, setBenefitFor] = useState<CardStatus | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    Promise.all([getCards(), getBestByCategory(), getCategories(), getAccounts()])
      .then(([c, b, cats, accs]) => {
        setCards(c);
        setBest(b);
        setCategories(cats);
        setAccounts(accs);
      })
      .catch(() => toast.error("카드 정보를 불러오지 못했어요"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(reload, [reload]);

  async function removeCard(card: CardStatus) {
    if (!window.confirm(`"${card.name}" 카드를 삭제할까요? (혜택도 함께 삭제)`)) return;
    try {
      await deleteCard(card.id);
      toast.success("삭제했어요");
      reload();
    } catch {
      toast.error("삭제 실패");
    }
  }

  async function removeBenefit(b: BenefitInfo) {
    try {
      await deleteCardBenefit(b.id);
      reload();
    } catch {
      toast.error("혜택 삭제 실패");
    }
  }

  return (
    <div className="mx-auto w-full max-w-xl">
      <ManageHeader
        title="카드 혜택"
        action={
          <Button size="sm" onClick={() => setCardOpen(true)}>
            <Plus className="size-4" />
            카드
          </Button>
        }
      />

      {loading ? (
        <div className="grid gap-3">
          <Skeleton className="h-40 w-full rounded-xl" />
          <Skeleton className="h-32 w-full rounded-xl" />
        </div>
      ) : (
        <div className="grid gap-5">
          {/* 카테고리별 최적 카드 */}
          {best.length > 0 && (
            <div className="grid gap-2">
              <h2 className="px-1 text-[13px] font-medium text-muted-foreground">
                카테고리별 최적 카드
              </h2>
              <Card className="gap-0 overflow-hidden py-0">
                {best.map((b) => (
                  <div
                    key={`${b.category_id}-${b.card_id}`}
                    className="flex items-center gap-3 border-b px-4 py-2.5 last:border-b-0"
                  >
                    <span className="flex-1 text-sm font-medium">{b.category_name}</span>
                    <span className="text-[13px] text-muted-foreground">{b.card_name}</span>
                    <span className="rounded-full bg-brand/10 px-2 py-0.5 text-[12px] font-semibold text-brand tabular-nums">
                      {ratePct(b.rate_bp)} {kindLabel(b.kind)}
                    </span>
                  </div>
                ))}
              </Card>
            </div>
          )}

          {/* 내 카드 */}
          <div className="grid gap-2">
            <h2 className="px-1 text-[13px] font-medium text-muted-foreground">내 카드</h2>
            {cards.length === 0 ? (
              <Card className="flex flex-col items-center gap-2 py-10 text-center">
                <span className="flex size-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
                  <CreditCard className="size-5" />
                </span>
                <p className="text-sm text-muted-foreground">
                  카드를 추가하면 결제마다 최적 카드를 알려드려요.
                </p>
              </Card>
            ) : (
              <div className="grid gap-3">
                {cards.map((card) => (
                  <CardItem
                    key={card.id}
                    card={card}
                    onAddBenefit={() => setBenefitFor(card)}
                    onDeleteCard={() => removeCard(card)}
                    onDeleteBenefit={removeBenefit}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <CardDialog
        open={cardOpen}
        onOpenChange={setCardOpen}
        accounts={accounts}
        onSaved={reload}
      />
      <BenefitDialog
        card={benefitFor}
        onOpenChange={(o) => !o && setBenefitFor(null)}
        categories={categories}
        onSaved={reload}
      />
    </div>
  );
}

function CardItem({
  card,
  onAddBenefit,
  onDeleteCard,
  onDeleteBenefit,
}: {
  card: CardStatus;
  onAddBenefit: () => void;
  onDeleteCard: () => void;
  onDeleteBenefit: (b: BenefitInfo) => void;
}) {
  const thr = card.performance_threshold;
  const usage = thr && thr > 0 ? card.monthly_spend / thr : null;
  return (
    <Card className="gap-0 p-4">
      <div className="flex items-start gap-2">
        <div className="flex-1">
          <p className="text-[15px] font-semibold">{card.name}</p>
          {card.issuer && (
            <p className="text-[11px] text-muted-foreground">{card.issuer}</p>
          )}
        </div>
        <button
          type="button"
          onClick={onDeleteCard}
          aria-label="카드 삭제"
          className="inline-flex size-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
        >
          <Trash2 className="size-4" />
        </button>
      </div>

      {/* 이번달 실적 */}
      {thr != null ? (
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-[12px]">
            <span className="text-muted-foreground">이번 달 실적</span>
            <span
              className={cn(
                "font-medium tabular-nums",
                card.threshold_met ? "text-emerald-600 dark:text-emerald-400" : "",
              )}
            >
              {card.threshold_met ? "실적 달성" : `${formatPercent(usage ?? 0)}`}
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={cn(
                "h-full rounded-full",
                card.threshold_met ? "bg-emerald-500" : "bg-brand",
              )}
              style={{ width: `${Math.min((usage ?? 0) * 100, 100)}%` }}
            />
          </div>
          <div className="mt-1 flex justify-between text-[11px] text-muted-foreground">
            <span>{formatManwon(card.monthly_spend)}</span>
            <span>기준 {formatManwon(thr)}</span>
          </div>
        </div>
      ) : (
        <p className="mt-2 text-[12px] text-muted-foreground">실적 조건 없음</p>
      )}

      {/* 혜택 칩 */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {card.benefits.map((b) => (
          <span
            key={b.id}
            className="group inline-flex items-center gap-1 rounded-full border py-1 pl-2.5 pr-1 text-[12px]"
          >
            <span className="font-medium">{b.category_name}</span>
            <span className="text-brand">
              {ratePct(b.rate_bp)} {kindLabel(b.kind)}
            </span>
            <button
              type="button"
              onClick={() => onDeleteBenefit(b)}
              aria-label="혜택 삭제"
              className="inline-flex size-4 items-center justify-center rounded-full text-muted-foreground hover:text-destructive"
            >
              <Trash2 className="size-3" />
            </button>
          </span>
        ))}
        <button
          type="button"
          onClick={onAddBenefit}
          className="inline-flex items-center gap-1 rounded-full border border-dashed px-2.5 py-1 text-[12px] text-muted-foreground transition-colors hover:bg-accent"
        >
          <Plus className="size-3" />
          혜택
        </button>
      </div>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-1.5">
      <span className="text-[12px] font-medium text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

function CardDialog({
  open,
  onOpenChange,
  accounts,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  accounts: Account[];
  onSaved: () => void;
}) {
  const [name, setName] = useState("");
  const [issuer, setIssuer] = useState("");
  const [accountId, setAccountId] = useState<string>("none");
  const [threshold, setThreshold] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setName("");
      setIssuer("");
      setAccountId("none");
      setThreshold("");
    }
  }, [open]);

  const accountItems = useMemo(
    () => ({
      none: "연결 안 함",
      ...Object.fromEntries(
        accounts.filter((a) => a.type === "card").map((a) => [String(a.id), a.name]),
      ),
    }),
    [accounts],
  );

  async function submit() {
    if (!name.trim()) {
      toast.error("카드 이름을 입력하세요");
      return;
    }
    setSaving(true);
    try {
      await createCard({
        name: name.trim(),
        issuer: issuer.trim() || null,
        account_id: accountId === "none" ? null : Number(accountId),
        performance_threshold: threshold ? Math.round(Number(threshold)) : null,
      });
      toast.success("카드를 추가했어요");
      onOpenChange(false);
      onSaved();
    } catch (e) {
      toast.error("추가 실패", {
        description: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm gap-4 rounded-2xl">
        <DialogHeader>
          <DialogTitle>카드 추가</DialogTitle>
        </DialogHeader>
        <div className="grid gap-3.5">
          <Field label="카드 이름">
            <Input
              placeholder="예: 현대카드 M"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </Field>
          <Field label="발행사 (선택)">
            <Input
              placeholder="예: 현대"
              value={issuer}
              onChange={(e) => setIssuer(e.target.value)}
            />
          </Field>
          <Field label="연결 계좌 (실적 계산용, 선택)">
            <Select
              items={accountItems}
              value={accountId}
              onValueChange={(v) => setAccountId(v ?? "none")}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">연결 안 함</SelectItem>
                {accounts
                  .filter((a) => a.type === "card")
                  .map((a) => (
                    <SelectItem key={a.id} value={String(a.id)}>
                      {a.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="전월실적 기준 (원, 선택)">
            <Input
              type="number"
              inputMode="numeric"
              placeholder="예: 300000"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              className="text-right tabular-nums"
            />
          </Field>
        </div>
        <DialogFooter>
          <Button className="w-full" disabled={saving} onClick={submit}>
            {saving ? "저장 중…" : "추가"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function BenefitDialog({
  card,
  onOpenChange,
  categories,
  onSaved,
}: {
  card: CardStatus | null;
  onOpenChange: (o: boolean) => void;
  categories: Category[];
  onSaved: () => void;
}) {
  const [categoryId, setCategoryId] = useState("all");
  const [kind, setKind] = useState<BenefitKind>("accrue");
  const [rate, setRate] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (card) {
      setCategoryId("all");
      setKind("accrue");
      setRate("");
    }
  }, [card]);

  const expense = useMemo(
    () => categories.filter((c) => c.kind === "expense"),
    [categories],
  );
  const categoryItems = useMemo(
    () => ({
      all: "전체 가맹점",
      ...Object.fromEntries(expense.map((c) => [String(c.id), c.name])),
    }),
    [expense],
  );

  async function submit() {
    if (!card) return;
    const pct = Number(rate);
    if (!pct || pct <= 0) {
      toast.error("적립/할인율을 입력하세요");
      return;
    }
    setSaving(true);
    try {
      await addCardBenefit(card.id, {
        category_id: categoryId === "all" ? null : Number(categoryId),
        kind,
        rate_bp: Math.round(pct * 100),
      });
      toast.success("혜택을 추가했어요");
      onOpenChange(false);
      onSaved();
    } catch (e) {
      toast.error("추가 실패", {
        description: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={card !== null} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm gap-4 rounded-2xl">
        <DialogHeader>
          <DialogTitle>{card?.name} · 혜택 추가</DialogTitle>
        </DialogHeader>
        <div className="grid gap-3.5">
          <div className="grid grid-cols-2 gap-1 rounded-xl bg-muted p-1">
            {(["accrue", "discount"] as BenefitKind[]).map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => setKind(k)}
                className={cn(
                  "rounded-lg py-1.5 text-sm font-medium transition-colors",
                  kind === k
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground",
                )}
              >
                {kindLabel(k)}
              </button>
            ))}
          </div>
          <Field label="카테고리">
            <Select
              items={categoryItems}
              value={categoryId}
              onValueChange={(v) => setCategoryId(v ?? "all")}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">전체 가맹점</SelectItem>
                {expense.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="적립/할인율 (%)">
            <Input
              type="number"
              inputMode="decimal"
              placeholder="예: 5"
              value={rate}
              onChange={(e) => setRate(e.target.value)}
              className="text-right tabular-nums"
              autoFocus
            />
          </Field>
        </div>
        <DialogFooter>
          <Button className="w-full" disabled={saving} onClick={submit}>
            {saving ? "저장 중…" : "추가"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
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
import {
  createTransaction,
  getAccounts,
  getCategories,
  type Account,
  type Category,
  type TxnType,
} from "@/lib/api";
import { cn } from "@/lib/utils";

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;
}

const AUTO = "__auto__";

export function AddTransaction({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);

  const [type, setType] = useState<TxnType>("expense");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(todayStr);
  const [merchant, setMerchant] = useState("");
  const [categoryId, setCategoryId] = useState<string>(AUTO);
  const [accountId, setAccountId] = useState<string>("");
  const [memo, setMemo] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // 다이얼로그 열릴 때 계좌·카테고리 로드
  useEffect(() => {
    if (!open) return;
    Promise.all([getAccounts(), getCategories()])
      .then(([accs, cats]) => {
        setAccounts(accs);
        setCategories(cats);
        if (accs.length && !accountId) setAccountId(String(accs[0].id));
      })
      .catch(() => toast.error("계좌/카테고리를 불러오지 못했어요"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const categoryOptions = useMemo(
    () => categories.filter((c) => c.kind === type),
    [categories, type],
  );

  // Base UI Select 는 items(값→라벨) 가 있어야 Value 에 라벨을 표시
  const accountItems = useMemo(
    () => Object.fromEntries(accounts.map((a) => [String(a.id), a.name])),
    [accounts],
  );
  const categoryItems = useMemo(
    () => ({
      [AUTO]: "자동 분류 (규칙엔진)",
      ...Object.fromEntries(categoryOptions.map((c) => [String(c.id), c.name])),
    }),
    [categoryOptions],
  );

  // 유형 바뀌면 카테고리 선택 초기화(자동)
  useEffect(() => setCategoryId(AUTO), [type]);

  function reset() {
    setType("expense");
    setAmount("");
    setDate(todayStr());
    setMerchant("");
    setCategoryId(AUTO);
    setMemo("");
  }

  async function submit() {
    const amt = Math.round(Number(amount));
    if (!amt || amt <= 0) {
      toast.error("금액을 입력하세요");
      return;
    }
    if (!accountId) {
      toast.error("계좌를 선택하세요");
      return;
    }
    setSubmitting(true);
    try {
      await createTransaction({
        account_id: Number(accountId),
        type,
        amount: amt,
        occurred_at: `${date}T12:00:00`,
        merchant: merchant.trim() || null,
        category_id: categoryId === AUTO ? null : Number(categoryId),
        memo: memo.trim() || null,
        source: "manual",
      });
      toast.success("거래를 추가했어요");
      reset();
      onOpenChange(false);
      onCreated();
    } catch (e) {
      toast.error("추가 실패", {
        description: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm gap-4 rounded-2xl">
        <DialogHeader>
          <DialogTitle>거래 추가</DialogTitle>
        </DialogHeader>

        <div className="grid gap-3.5">
          {/* 유형 토글 */}
          <div className="grid grid-cols-2 gap-1 rounded-xl bg-muted p-1">
            {(["expense", "income"] as TxnType[]).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setType(t)}
                className={cn(
                  "rounded-lg py-1.5 text-sm font-medium transition-colors",
                  type === t
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground",
                )}
              >
                {t === "expense" ? "지출" : "수입"}
              </button>
            ))}
          </div>

          {/* 금액 */}
          <Field label="금액 (원)">
            <Input
              type="number"
              inputMode="numeric"
              placeholder="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="text-right tabular-nums"
              autoFocus
            />
          </Field>

          {/* 날짜 */}
          <Field label="날짜">
            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </Field>

          {/* 가맹점 */}
          <Field label={type === "expense" ? "가맹점" : "내용"}>
            <Input
              placeholder={type === "expense" ? "예: 스타벅스 강남점" : "예: 급여 입금"}
              value={merchant}
              onChange={(e) => setMerchant(e.target.value)}
            />
          </Field>

          {/* 계좌 */}
          <Field label="계좌">
            <Select
              items={accountItems}
              value={accountId}
              onValueChange={(v) => setAccountId(v ?? "")}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="계좌 선택" />
              </SelectTrigger>
              <SelectContent>
                {accounts.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>
                    {a.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          {/* 카테고리 */}
          <Field label="카테고리">
            <Select
              items={categoryItems}
              value={categoryId}
              onValueChange={(v) => setCategoryId(v ?? AUTO)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={AUTO}>자동 분류 (규칙엔진)</SelectItem>
                {categoryOptions.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          {/* 메모 */}
          <Field label="메모 (선택)">
            <Input
              placeholder="메모"
              value={memo}
              onChange={(e) => setMemo(e.target.value)}
            />
          </Field>
        </div>

        <DialogFooter>
          <Button
            type="button"
            className="w-full"
            disabled={submitting}
            onClick={submit}
          >
            {submitting ? "추가 중…" : "추가"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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

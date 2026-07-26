"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowRight, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

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
  createCategoryRule,
  deleteCategoryRule,
  getCategories,
  getCategoryRules,
  updateCategoryRule,
  type Category,
  type CategoryRule,
  type MatchType,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const MATCH_LABEL: Record<MatchType, string> = {
  contains: "포함",
  exact: "일치",
  regex: "정규식",
};

export default function RulesPage() {
  const [rules, setRules] = useState<CategoryRule[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<CategoryRule | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    Promise.all([getCategoryRules(), getCategories()])
      .then(([r, c]) => {
        setRules([...r].sort((a, b) => b.priority - a.priority || a.id - b.id));
        setCategories(c);
      })
      .catch(() => toast.error("규칙을 불러오지 못했어요"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(reload, [reload]);

  const catName = useMemo(
    () => new Map(categories.map((c) => [c.id, c.name])),
    [categories],
  );

  async function toggle(rule: CategoryRule) {
    try {
      await updateCategoryRule(rule.id, { enabled: !rule.enabled });
      reload();
    } catch {
      toast.error("변경 실패");
    }
  }

  async function remove(rule: CategoryRule) {
    if (!window.confirm(`규칙 "${rule.pattern}"을 삭제할까요?`)) return;
    try {
      await deleteCategoryRule(rule.id);
      toast.success("삭제했어요");
      reload();
    } catch (e) {
      toast.error("삭제 실패", {
        description: e instanceof Error ? e.message : String(e),
      });
    }
  }

  return (
    <div className="mx-auto w-full max-w-xl">
      <ManageHeader
        title="자동분류 규칙"
        action={
          <Button
            size="sm"
            onClick={() => {
              setEditing(null);
              setDialogOpen(true);
            }}
          >
            <Plus className="size-4" />
            추가
          </Button>
        }
      />
      <p className="mb-4 px-1 text-[12px] text-muted-foreground">
        가맹점명이 패턴과 맞으면 해당 카테고리로 자동 분류돼요. 우선순위가 높은 규칙이 먼저
        적용됩니다.
      </p>

      {loading ? (
        <div className="grid gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <Card className="gap-0 overflow-hidden py-0">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className={cn(
                "flex items-center gap-2 border-b px-4 py-2.5 last:border-b-0",
                !rule.enabled && "opacity-45",
              )}
            >
              <span className="w-7 shrink-0 text-center text-[11px] font-medium tabular-nums text-muted-foreground">
                {rule.priority}
              </span>
              <div className="flex min-w-0 flex-1 items-center gap-1.5">
                <span className="truncate text-sm font-medium">{rule.pattern}</span>
                <span className="shrink-0 rounded border px-1 py-0.5 text-[9px] text-muted-foreground">
                  {MATCH_LABEL[rule.match_type]}
                </span>
                <ArrowRight className="size-3 shrink-0 text-muted-foreground" />
                <span className="truncate text-[13px] text-muted-foreground">
                  {catName.get(rule.category_id) ?? "?"}
                </span>
              </div>
              <button
                type="button"
                onClick={() => toggle(rule)}
                aria-label={rule.enabled ? "비활성화" : "활성화"}
                className={cn(
                  "relative h-5 w-9 shrink-0 rounded-full transition-colors",
                  rule.enabled ? "bg-brand" : "bg-muted-foreground/30",
                )}
              >
                <span
                  className={cn(
                    "absolute top-0.5 size-4 rounded-full bg-white transition-all",
                    rule.enabled ? "left-[18px]" : "left-0.5",
                  )}
                />
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditing(rule);
                  setDialogOpen(true);
                }}
                aria-label="수정"
                className="inline-flex size-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                <Pencil className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => remove(rule)}
                aria-label="삭제"
                className="inline-flex size-8 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
              >
                <Trash2 className="size-4" />
              </button>
            </div>
          ))}
        </Card>
      )}

      <RuleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editing={editing}
        categories={categories}
        onSaved={reload}
      />
    </div>
  );
}

function RuleDialog({
  open,
  onOpenChange,
  editing,
  categories,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  editing: CategoryRule | null;
  categories: Category[];
  onSaved: () => void;
}) {
  const [pattern, setPattern] = useState("");
  const [matchType, setMatchType] = useState<MatchType>("contains");
  const [categoryId, setCategoryId] = useState("");
  const [priority, setPriority] = useState("1");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setPattern(editing?.pattern ?? "");
      setMatchType(editing?.match_type ?? "contains");
      setCategoryId(editing ? String(editing.category_id) : "");
      setPriority(String(editing?.priority ?? 1));
    }
  }, [open, editing]);

  const categoryItems = useMemo(
    () => Object.fromEntries(categories.map((c) => [String(c.id), c.name])),
    [categories],
  );
  const matchItems: Record<MatchType, string> = {
    contains: "포함 (가맹점에 이 단어가 있으면)",
    exact: "정확히 일치",
    regex: "정규식",
  };

  async function submit() {
    if (!pattern.trim()) {
      toast.error("패턴을 입력하세요");
      return;
    }
    if (!categoryId) {
      toast.error("카테고리를 선택하세요");
      return;
    }
    setSaving(true);
    const payload = {
      pattern: pattern.trim(),
      match_type: matchType,
      category_id: Number(categoryId),
      priority: Math.round(Number(priority)) || 0,
    };
    try {
      if (editing) await updateCategoryRule(editing.id, payload);
      else await createCategoryRule(payload);
      toast.success(editing ? "수정했어요" : "추가했어요");
      onOpenChange(false);
      onSaved();
    } catch (e) {
      toast.error("저장 실패", {
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
          <DialogTitle>{editing ? "규칙 수정" : "규칙 추가"}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-3.5">
          <Field label="패턴 (가맹점 키워드)">
            <Input
              placeholder="예: 스타벅스"
              value={pattern}
              onChange={(e) => setPattern(e.target.value)}
              autoFocus
            />
          </Field>
          <Field label="매칭 방식">
            <Select
              items={matchItems}
              value={matchType}
              onValueChange={(v) => setMatchType((v as MatchType) ?? "contains")}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(matchItems) as MatchType[]).map((k) => (
                  <SelectItem key={k} value={k}>
                    {matchItems[k]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="카테고리">
            <Select
              items={categoryItems}
              value={categoryId}
              onValueChange={(v) => setCategoryId(v ?? "")}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="카테고리 선택" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field label="우선순위 (높을수록 먼저 적용)">
            <Input
              type="number"
              inputMode="numeric"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="text-right tabular-nums"
            />
          </Field>
        </div>
        <DialogFooter>
          <Button className="w-full" disabled={saving} onClick={submit}>
            {saving ? "저장 중…" : editing ? "저장" : "추가"}
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

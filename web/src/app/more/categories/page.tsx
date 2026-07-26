"use client";

import { useCallback, useEffect, useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  createCategory,
  deleteCategory,
  getCategories,
  updateCategory,
  type Category,
  type CategoryKind,
} from "@/lib/api";
import { categoryIcon } from "@/lib/categories";
import { cn } from "@/lib/utils";

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    getCategories()
      .then(setCategories)
      .catch(() => toast.error("카테고리를 불러오지 못했어요"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(reload, [reload]);

  function openAdd() {
    setEditing(null);
    setDialogOpen(true);
  }
  function openEdit(cat: Category) {
    setEditing(cat);
    setDialogOpen(true);
  }

  async function remove(cat: Category) {
    if (!window.confirm(`"${cat.name}" 카테고리를 삭제할까요?`)) return;
    try {
      await deleteCategory(cat.id);
      toast.success("삭제했어요");
      reload();
    } catch (e) {
      toast.error("삭제 실패", {
        description: e instanceof Error ? e.message : String(e),
      });
    }
  }

  const expense = categories.filter((c) => c.kind === "expense");
  const income = categories.filter((c) => c.kind === "income");

  return (
    <div className="mx-auto w-full max-w-xl">
      <ManageHeader
        title="카테고리"
        action={
          <Button size="sm" onClick={openAdd}>
            <Plus className="size-4" />
            추가
          </Button>
        }
      />

      {loading ? (
        <div className="grid gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-5">
          <Section title="지출" items={expense} onEdit={openEdit} onDelete={remove} />
          <Section title="수입" items={income} onEdit={openEdit} onDelete={remove} />
        </div>
      )}

      <CategoryDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editing={editing}
        onSaved={reload}
      />
    </div>
  );
}

function Section({
  title,
  items,
  onEdit,
  onDelete,
}: {
  title: string;
  items: Category[];
  onEdit: (c: Category) => void;
  onDelete: (c: Category) => void;
}) {
  if (items.length === 0) return null;
  return (
    <div className="grid gap-2">
      <h2 className="px-1 text-[13px] font-medium text-muted-foreground">{title}</h2>
      <Card className="gap-0 overflow-hidden py-0">
        {items.map((cat) => {
          const Icon = categoryIcon(cat.name);
          return (
            <div
              key={cat.id}
              className="flex items-center gap-3 border-b px-4 py-2.5 last:border-b-0"
            >
              <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <Icon className="size-[16px]" />
              </span>
              <span className="flex-1 text-sm font-medium">{cat.name}</span>
              {cat.is_fixed && (
                <span className="rounded-full border px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                  고정
                </span>
              )}
              <button
                type="button"
                onClick={() => onEdit(cat)}
                aria-label="수정"
                className="inline-flex size-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                <Pencil className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => onDelete(cat)}
                aria-label="삭제"
                className="inline-flex size-8 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
              >
                <Trash2 className="size-4" />
              </button>
            </div>
          );
        })}
      </Card>
    </div>
  );
}

function CategoryDialog({
  open,
  onOpenChange,
  editing,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  editing: Category | null;
  onSaved: () => void;
}) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState<CategoryKind>("expense");
  const [isFixed, setIsFixed] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setName(editing?.name ?? "");
      setKind(editing?.kind ?? "expense");
      setIsFixed(editing?.is_fixed ?? false);
    }
  }, [open, editing]);

  async function submit() {
    if (!name.trim()) {
      toast.error("이름을 입력하세요");
      return;
    }
    setSaving(true);
    try {
      if (editing) {
        await updateCategory(editing.id, { name: name.trim(), kind, is_fixed: isFixed });
      } else {
        await createCategory({ name: name.trim(), kind, is_fixed: isFixed });
      }
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
          <DialogTitle>{editing ? "카테고리 수정" : "카테고리 추가"}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-3.5">
          <div className="grid grid-cols-2 gap-1 rounded-xl bg-muted p-1">
            {(["expense", "income"] as CategoryKind[]).map((k) => (
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
                {k === "expense" ? "지출" : "수입"}
              </button>
            ))}
          </div>

          <label className="grid gap-1.5">
            <span className="text-[12px] font-medium text-muted-foreground">이름</span>
            <Input
              placeholder="예: 반려동물"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </label>

          <button
            type="button"
            onClick={() => setIsFixed((v) => !v)}
            className="flex items-center justify-between rounded-lg border px-3 py-2.5 text-left"
          >
            <span className="text-sm">
              고정지출
              <span className="ml-1.5 text-[11px] text-muted-foreground">
                (매달 나가는 비용)
              </span>
            </span>
            <span
              className={cn(
                "relative h-5 w-9 rounded-full transition-colors",
                isFixed ? "bg-brand" : "bg-muted-foreground/30",
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 size-4 rounded-full bg-white transition-all",
                  isFixed ? "left-[18px]" : "left-0.5",
                )}
              />
            </span>
          </button>
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

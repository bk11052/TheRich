"use client";

import { useEffect, useMemo, useState } from "react";
import { ImagePlus, X } from "lucide-react";
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
  createPlace,
  createTag,
  getTransactions,
  setTransactionTags,
  updateTransaction,
  uploadPhoto,
  type Tag,
  type Transaction,
} from "@/lib/api";
import { formatManwon } from "@/lib/format";
import { cn } from "@/lib/utils";

function txnLabel(t: Transaction): string {
  const d = new Date(t.occurred_at);
  return `${t.merchant ?? "(미상)"} · ${d.getMonth() + 1}.${d.getDate()} · ₩${formatManwon(t.amount)}`;
}

export function AddRecord({
  open,
  onOpenChange,
  tags,
  onCreated,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  tags: Tag[];
  onCreated: () => void;
}) {
  const [txns, setTxns] = useState<Transaction[]>([]);
  const [txnId, setTxnId] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [placeName, setPlaceName] = useState("");
  const [region, setRegion] = useState("");
  const [memo, setMemo] = useState("");
  const [allTags, setAllTags] = useState<Tag[]>(tags);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [newTag, setNewTag] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    setAllTags(tags);
    getTransactions({ limit: 50 })
      .then(setTxns)
      .catch(() => toast.error("거래를 불러오지 못했어요"));
  }, [open, tags]);

  // 미리보기 object URL
  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files]);
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews]);

  const txnItems = useMemo(
    () => Object.fromEntries(txns.map((t) => [String(t.id), txnLabel(t)])),
    [txns],
  );

  function reset() {
    setTxnId("");
    setFiles([]);
    setPlaceName("");
    setRegion("");
    setMemo("");
    setSelected(new Set());
    setNewTag("");
  }

  function toggleTag(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function addNewTag() {
    const name = newTag.trim();
    if (!name) return;
    try {
      const t = await createTag({ name });
      setAllTags((prev) => [...prev, t]);
      setSelected((prev) => new Set(prev).add(t.id));
      setNewTag("");
    } catch {
      toast.error("태그 추가 실패");
    }
  }

  async function submit() {
    if (!txnId) {
      toast.error("거래를 선택하세요");
      return;
    }
    const id = Number(txnId);
    setSaving(true);
    try {
      let placeId: number | undefined;
      if (placeName.trim()) {
        const place = await createPlace({
          name: placeName.trim(),
          region: region.trim() || null,
        });
        placeId = place.id;
      }
      if (placeId != null || memo.trim()) {
        await updateTransaction(id, {
          ...(placeId != null ? { place_id: placeId } : {}),
          ...(memo.trim() ? { memo: memo.trim() } : {}),
        });
      }
      for (const f of files) {
        await uploadPhoto(f, id);
      }
      if (selected.size > 0) {
        await setTransactionTags(id, [...selected]);
      }
      toast.success("기록을 추가했어요");
      reset();
      onOpenChange(false);
      onCreated();
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
      <DialogContent className="max-h-[88dvh] max-w-sm gap-4 overflow-y-auto rounded-2xl">
        <DialogHeader>
          <DialogTitle>기록 추가</DialogTitle>
        </DialogHeader>

        <div className="grid gap-3.5">
          {/* 거래 선택 */}
          <Field label="거래">
            <Select items={txnItems} value={txnId} onValueChange={(v) => setTxnId(v ?? "")}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="거래 선택" />
              </SelectTrigger>
              <SelectContent>
                {txns.map((t) => (
                  <SelectItem key={t.id} value={String(t.id)}>
                    {txnLabel(t)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          {/* 사진 */}
          <Field label="사진">
            <div className="flex flex-wrap gap-2">
              {previews.map((url, i) => (
                <div key={url} className="relative size-20 overflow-hidden rounded-lg">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={url} alt="" className="size-full object-cover" />
                  <button
                    type="button"
                    onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}
                    className="absolute right-0.5 top-0.5 inline-flex size-5 items-center justify-center rounded-full bg-black/60 text-white"
                    aria-label="사진 제거"
                  >
                    <X className="size-3" />
                  </button>
                </div>
              ))}
              <label className="flex size-20 cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-dashed text-muted-foreground transition-colors hover:bg-accent">
                <ImagePlus className="size-5" />
                <span className="text-[10px]">추가</span>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={(e) => {
                    const picked = Array.from(e.target.files ?? []);
                    if (picked.length) setFiles((prev) => [...prev, ...picked]);
                    e.target.value = "";
                  }}
                />
              </label>
            </div>
          </Field>

          {/* 장소 */}
          <Field label="장소 (선택)">
            <Input
              placeholder="예: 성수동 삼겹살"
              value={placeName}
              onChange={(e) => setPlaceName(e.target.value)}
            />
          </Field>
          {placeName.trim() && (
            <Field label="지역 (선택)">
              <Input
                placeholder="예: 성수동"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              />
            </Field>
          )}

          {/* 태그 */}
          <Field label="태그">
            <div className="flex flex-wrap gap-1.5">
              {allTags.map((t) => {
                const on = selected.has(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => toggleTag(t.id)}
                    className={cn(
                      "flex items-center gap-1 rounded-full border px-2.5 py-1 text-[12px] font-medium transition-colors",
                      on ? "border-brand bg-brand/10 text-brand" : "text-muted-foreground",
                    )}
                  >
                    {t.color && (
                      <span
                        className="size-2 rounded-full"
                        style={{ backgroundColor: t.color }}
                      />
                    )}
                    {t.name}
                  </button>
                );
              })}
            </div>
            <div className="mt-2 flex gap-2">
              <Input
                placeholder="새 태그"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addNewTag();
                  }
                }}
                className="h-8"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addNewTag}
                disabled={!newTag.trim()}
              >
                추가
              </Button>
            </div>
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
          <Button className="w-full" disabled={saving} onClick={submit}>
            {saving ? "저장 중…" : "기록 추가"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <span className="text-[12px] font-medium text-muted-foreground">{label}</span>
      {children}
    </div>
  );
}

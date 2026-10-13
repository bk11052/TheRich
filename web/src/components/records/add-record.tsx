"use client";

import { useEffect, useMemo, useRef, useState } from "react";
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
  attachSharedPlace,
  createSharedTag,
  getSharedTransactions,
  setSharedTransactionMemo,
  setSharedTransactionTags,
  uploadSharedPhoto,
  type SharedTransaction,
  type Tag,
} from "@/lib/api";
import { formatManwon } from "@/lib/format";
import { addMonth, currentMonth } from "@/lib/month";
import { cn } from "@/lib/utils";

/** 기록은 보통 최근 데이트에 붙이므로 이번 달·지난달 데이트비용 거래를 후보로. */
async function recentSharedTxns(): Promise<SharedTransaction[]> {
  const now = currentMonth();
  const [a, b] = await Promise.all([
    getSharedTransactions(now),
    getSharedTransactions(addMonth(now, -1)),
  ]);
  return [...a, ...b];
}

function txnLabel(t: SharedTransaction): string {
  const d = new Date(t.occurred_at);
  return `${t.merchant ?? "(미상)"} · ${d.getMonth() + 1}.${d.getDate()} · ₩${formatManwon(t.amount)}`;
}

export function AddRecord({
  open,
  onOpenChange,
  tags,
  onCreated,
  initialTxn = null,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  tags: Tag[];
  onCreated: () => void;
  /** 데이트비용 탭에서 지출을 눌러 들어온 경우, 그 거래를 미리 고른 채로 연다. */
  initialTxn?: SharedTransaction | null;
}) {
  const [txns, setTxns] = useState<SharedTransaction[]>([]);
  const [txnId, setTxnId] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [placeName, setPlaceName] = useState("");
  const [region, setRegion] = useState("");
  const [memo, setMemo] = useState("");
  const [allTags, setAllTags] = useState<Tag[]>(tags);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [newTag, setNewTag] = useState("");
  const [saving, setSaving] = useState(false);
  // 연결로 들어와 '자동으로' 고른 거래 id. 창은 닫아도 입력 중이던 내용을 남겨두지만,
  // 이 자동 선택까지 남으면 다음에 '+ 기록'으로 열 때 엉뚱한 거래가 골라져 있다.
  const autoTxnId = useRef<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setAllTags(tags);
    recentSharedTxns()
      .then((list) => {
        // 후보는 최근 두 달뿐이라, 더 오래된 지출을 눌러 왔으면 목록에 직접 끼워 넣는다.
        // (목록에 없는 값은 선택 상자가 표시하지 못한다)
        if (initialTxn && !list.some((t) => t.id === initialTxn.id)) list = [initialTxn, ...list];
        setTxns(list);
        if (initialTxn) {
          autoTxnId.current = String(initialTxn.id);
          setTxnId(autoTxnId.current);
        } else if (autoTxnId.current) {
          // 지난번 자동 선택이 그대로라면 비운다. 사용자가 직접 바꿨다면 그 선택은 존중.
          const auto = autoTxnId.current;
          autoTxnId.current = null;
          setTxnId((cur) => (cur === auto ? "" : cur));
        }
      })
      .catch(() => toast.error("거래를 불러오지 못했어요"));
  }, [open, tags, initialTxn]);

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
      const t = await createSharedTag({ name });
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
      if (placeName.trim()) {
        await attachSharedPlace(id, { name: placeName.trim(), region: region.trim() || null });
      }
      if (memo.trim()) {
        await setSharedTransactionMemo(id, memo.trim());
      }
      for (const f of files) {
        await uploadSharedPhoto(f, id);
      }
      if (selected.size > 0) {
        await setSharedTransactionTags(id, [...selected]);
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

"use client";

import { useCallback, useEffect, useState } from "react";
import { ImageIcon, LayoutGrid, Map, MapPin, Plus } from "lucide-react";
import { toast } from "sonner";

import { Amount } from "@/components/amount";
import { AddRecord } from "@/components/records/add-record";
import { RecordDetail } from "@/components/records/record-detail";
import { RecordsMap } from "@/components/records/records-map";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getRecords, getTags, photoUrl, type RecordItem, type Tag } from "@/lib/api";
import { categoryIcon } from "@/lib/categories";
import { cn } from "@/lib/utils";

function shortDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}.${d.getDate()}`;
}

export default function RecordsPage() {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [activeTag, setActiveTag] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [detail, setDetail] = useState<RecordItem | null>(null);
  const [view, setView] = useState<"gallery" | "map">("gallery");

  const reload = useCallback(() => {
    setLoading(true);
    Promise.all([getRecords(activeTag != null ? { tag_id: activeTag } : {}), getTags()])
      .then(([recs, tgs]) => {
        setRecords(recs);
        setTags(tgs);
      })
      .catch(() => toast.error("기록을 불러오지 못했어요"))
      .finally(() => setLoading(false));
  }, [activeTag]);

  useEffect(reload, [reload]);

  return (
    <div className="grid gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold tracking-tight">기록</h1>
        <button
          type="button"
          onClick={() => setAddOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-full bg-brand px-4 py-2 text-sm font-semibold text-brand-foreground transition-transform active:scale-95"
        >
          <Plus className="size-4" />
          기록
        </button>
      </div>

      {/* 태그 필터 */}
      {tags.length > 0 && (
        <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 lg:mx-0 lg:px-0">
          <FilterChip
            label="전체"
            active={activeTag === null}
            onClick={() => setActiveTag(null)}
          />
          {tags.map((t) => (
            <FilterChip
              key={t.id}
              label={t.name}
              color={t.color}
              active={activeTag === t.id}
              onClick={() => setActiveTag(t.id)}
            />
          ))}
        </div>
      )}

      {/* 갤러리 / 지도 토글 */}
      <div className="flex justify-end">
        <div className="inline-flex rounded-lg border p-0.5">
          {(
            [
              { key: "gallery", icon: LayoutGrid, label: "갤러리" },
              { key: "map", icon: Map, label: "지도" },
            ] as const
          ).map(({ key, icon: Icon, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => setView(key)}
              aria-label={label}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] font-medium transition-colors",
                view === key
                  ? "bg-brand/10 text-brand"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icon className="size-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="aspect-square w-full rounded-xl" />
          ))}
        </div>
      ) : view === "map" ? (
        <RecordsMap records={records} onSelect={setDetail} />
      ) : records.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 py-14 text-center">
          <span className="flex size-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
            <ImageIcon className="size-6" />
          </span>
          <p className="text-sm font-medium">아직 기록이 없어요</p>
          <p className="max-w-xs text-[13px] text-muted-foreground">
            거래에 사진·장소·태그를 붙여 맛집과 추억을 남겨보세요.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {records.map((r) => (
            <RecordCard key={r.id} record={r} onClick={() => setDetail(r)} />
          ))}
        </div>
      )}

      <AddRecord open={addOpen} onOpenChange={setAddOpen} tags={tags} onCreated={reload} />
      <RecordDetail record={detail} onClose={() => setDetail(null)} />
    </div>
  );
}

function FilterChip({
  label,
  color,
  active,
  onClick,
}: {
  label: string;
  color?: string | null;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-[13px] font-medium transition-colors",
        active
          ? "border-brand bg-brand/10 text-brand"
          : "text-muted-foreground hover:bg-accent",
      )}
    >
      {color && (
        <span className="size-2 rounded-full" style={{ backgroundColor: color }} />
      )}
      {label}
    </button>
  );
}

function RecordCard({ record, onClick }: { record: RecordItem; onClick: () => void }) {
  const photo = record.photos[0];
  const Icon = categoryIcon(undefined);
  const title = record.place?.name ?? record.merchant ?? "(기록)";
  return (
    <button type="button" onClick={onClick} className="group text-left">
      <div className="relative aspect-square overflow-hidden rounded-xl bg-muted">
        {photo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={photoUrl(photo.file_path)}
            alt={title}
            className="size-full object-cover transition-transform group-hover:scale-[1.03]"
          />
        ) : (
          <div className="flex size-full items-center justify-center text-muted-foreground">
            <Icon className="size-8" />
          </div>
        )}
        {record.photos.length > 1 && (
          <span className="absolute right-1.5 top-1.5 rounded-full bg-black/55 px-1.5 py-0.5 text-[10px] font-medium text-white">
            {record.photos.length}
          </span>
        )}
        {record.tags.length > 0 && (
          <div className="absolute bottom-1.5 left-1.5 flex flex-wrap gap-1">
            {record.tags.slice(0, 2).map((t) => (
              <span
                key={t.id}
                className="rounded-full bg-black/55 px-1.5 py-0.5 text-[10px] font-medium text-white"
              >
                {t.name}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="mt-1.5 px-0.5">
        <p className="flex items-center gap-0.5 truncate text-[13px] font-medium">
          {record.place && <MapPin className="size-3 shrink-0 text-muted-foreground" />}
          <span className="truncate">{title}</span>
        </p>
        <div className="flex items-center justify-between text-[11px] text-muted-foreground">
          <span>{shortDate(record.occurred_at)}</span>
          <Amount value={record.amount} compact />
        </div>
      </div>
    </button>
  );
}

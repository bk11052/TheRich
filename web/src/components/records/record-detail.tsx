"use client";

import { MapPin } from "lucide-react";

import { Amount } from "@/components/amount";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { photoUrl, type RecordItem } from "@/lib/api";

function longDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getFullYear()}.${d.getMonth() + 1}.${d.getDate()}`;
}

export function RecordDetail({
  record,
  onClose,
}: {
  record: RecordItem | null;
  onClose: () => void;
}) {
  return (
    <Dialog open={record !== null} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-md gap-4 rounded-2xl">
        {record && (
          <>
            <DialogHeader>
              <DialogTitle>{record.place?.name ?? record.merchant ?? "기록"}</DialogTitle>
            </DialogHeader>

            {record.photos.length > 0 && (
              <div className="-mx-1 flex gap-2 overflow-x-auto px-1">
                {record.photos.map((p) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    key={p.id}
                    src={photoUrl(p.file_path)}
                    alt=""
                    className="h-56 w-auto shrink-0 rounded-xl object-cover"
                  />
                ))}
              </div>
            )}

            <div className="grid gap-2 text-sm">
              <Row label="날짜" value={longDate(record.occurred_at)} />
              <Row label="금액" value={<Amount value={record.amount} className="font-semibold" />} />
              {record.merchant && <Row label="가맹점" value={record.merchant} />}
              {record.place?.region && <Row label="지역" value={record.place.region} />}
              {record.place?.address && (
                <Row
                  label="주소"
                  value={
                    <span className="flex items-center gap-1">
                      <MapPin className="size-3.5 text-muted-foreground" />
                      {record.place.address}
                    </span>
                  }
                />
              )}
              {record.memo && <Row label="메모" value={record.memo} />}
            </div>

            {record.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {record.tags.map((t) => (
                  <span
                    key={t.id}
                    className="flex items-center gap-1 rounded-full border px-2.5 py-1 text-[12px] font-medium"
                  >
                    {t.color && (
                      <span
                        className="size-2 rounded-full"
                        style={{ backgroundColor: t.color }}
                      />
                    )}
                    {t.name}
                  </span>
                ))}
              </div>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="shrink-0 text-muted-foreground">{label}</span>
      <span className="text-right">{value}</span>
    </div>
  );
}

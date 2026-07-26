"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { MapPin } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { RecordItem } from "@/lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
declare global {
  interface Window {
    kakao: any;
  }
}

const JS_KEY = process.env.NEXT_PUBLIC_KAKAO_JS_KEY;

let sdkPromise: Promise<any> | null = null;

function loadKakao(key: string): Promise<any> {
  if (typeof window !== "undefined" && window.kakao?.maps) {
    return Promise.resolve(window.kakao);
  }
  if (sdkPromise) return sdkPromise;
  sdkPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${key}&autoload=false`;
    script.async = true;
    script.onload = () => window.kakao.maps.load(() => resolve(window.kakao));
    script.onerror = () => reject(new Error("kakao sdk load failed"));
    document.head.appendChild(script);
  });
  return sdkPromise;
}

function Empty({ note }: { note: string }) {
  return (
    <Card className="flex flex-col items-center gap-2 py-14 text-center">
      <span className="flex size-14 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        <MapPin className="size-6" />
      </span>
      <p className="max-w-xs text-[13px] text-muted-foreground">{note}</p>
    </Card>
  );
}

export function RecordsMap({
  records,
  onSelect,
}: {
  records: RecordItem[];
  onSelect: (r: RecordItem) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);

  const withCoords = useMemo(
    () => records.filter((r) => r.place?.lat != null && r.place?.lng != null),
    [records],
  );

  useEffect(() => {
    if (!JS_KEY || !ref.current || withCoords.length === 0) return;
    let cancelled = false;
    loadKakao(JS_KEY)
      .then((kakao) => {
        if (cancelled || !ref.current) return;
        const first = withCoords[0].place!;
        const map = new kakao.maps.Map(ref.current, {
          center: new kakao.maps.LatLng(first.lat, first.lng),
          level: 7,
        });
        const bounds = new kakao.maps.LatLngBounds();
        for (const r of withCoords) {
          const pos = new kakao.maps.LatLng(r.place!.lat, r.place!.lng);
          const marker = new kakao.maps.Marker({ position: pos, map });
          kakao.maps.event.addListener(marker, "click", () => onSelect(r));
          bounds.extend(pos);
        }
        if (withCoords.length > 1) map.setBounds(bounds);
      })
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
    };
  }, [withCoords, onSelect]);

  if (!JS_KEY) {
    return (
      <Empty note="지도를 보려면 카카오 JavaScript 키를 web/.env.local 의 NEXT_PUBLIC_KAKAO_JS_KEY 에 넣어주세요." />
    );
  }
  if (error) {
    return (
      <Empty note="지도를 불러오지 못했어요. 카카오 앱 > 플랫폼 > Web 에 http://localhost:3000 을 등록했는지 확인하세요." />
    );
  }
  if (withCoords.length === 0) {
    return (
      <Empty note="좌표가 있는 기록이 없어요. 카카오 REST 키를 넣으면 장소 저장 시 좌표가 자동으로 채워져요." />
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border">
      <div ref={ref} className="h-[68dvh] w-full" />
    </div>
  );
}

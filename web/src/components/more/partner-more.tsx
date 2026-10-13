"use client";

import { useEffect, useState } from "react";
import { Check, MessageCircle } from "lucide-react";
import { toast } from "sonner";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getSharedMe, updateSharedMe, type SharedMe } from "@/lib/api";
import { HEX_COLOR, MEMBER_PALETTE } from "@/lib/palette";
import { cn } from "@/lib/utils";

/** partner 의 더보기: 본인 설정만. owner 의 관리 화면은 노출하지 않는다. */
export function PartnerMore() {
  const [me, setMe] = useState<SharedMe | null>(null);

  useEffect(() => {
    getSharedMe()
      .then(setMe)
      .catch(() => toast.error("내 정보를 불러오지 못했어요"));
  }, []);

  async function pick(color: string) {
    if (!me || !HEX_COLOR.test(color) || color === me.color) return;
    const prev = me;
    setMe({ ...me, color }); // 고르는 즉시 반영
    try {
      setMe(await updateSharedMe({ color }));
    } catch {
      setMe(prev);
      toast.error("색을 바꾸지 못했어요");
    }
  }

  return (
    <div className="mx-auto grid w-full max-w-xl gap-5">
      <div className="grid gap-2">
        <h2 className="px-1 text-[13px] font-medium text-muted-foreground">내 정보</h2>
        <Card className="gap-0 p-4">
          {me === null ? (
            <Skeleton className="h-16 w-full" />
          ) : (
            <>
              <div className="flex items-center gap-3">
                <span
                  aria-hidden
                  className="size-3.5 shrink-0 rounded-full ring-1 ring-black/10"
                  style={{ backgroundColor: me.color ?? "var(--muted-foreground)" }}
                />
                <p className="text-[15px] font-medium">{me.name}</p>
              </div>
              <p className="mt-3 text-[12px] text-muted-foreground">
                기록·내역에서 내가 올린 걸 구분하는 색이에요.
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {MEMBER_PALETTE.map((c) => (
                  <button
                    key={c}
                    type="button"
                    aria-label={`색 ${c}`}
                    aria-pressed={me.color === c}
                    onClick={() => pick(c)}
                    className={cn(
                      "flex size-7 items-center justify-center rounded-full ring-1 ring-black/10 transition",
                      me.color === c && "ring-2 ring-foreground ring-offset-2 ring-offset-background",
                    )}
                    style={{ backgroundColor: c }}
                  >
                    {me.color === c && <Check className="size-3.5 text-white" />}
                  </button>
                ))}
                <Input
                  key={me.color ?? ""}
                  defaultValue={me.color ?? ""}
                  placeholder="#2f6df6"
                  onBlur={(e) => pick(e.target.value.trim())}
                  className="h-7 w-24 text-[12px] tabular-nums"
                />
              </div>
            </>
          )}
        </Card>
      </div>

      <div className="grid gap-2">
        <h2 className="px-1 text-[13px] font-medium text-muted-foreground">텔레그램으로 올리기</h2>
        <Card className="gap-0 p-4">
          <div className="flex gap-3">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <MessageCircle className="size-[18px]" />
            </span>
            <div className="text-[13px] leading-relaxed">
              <p className="font-medium">봇에 &quot;가맹점 금액&quot;을 보내면 데이트비용으로 기록돼요.</p>
              <p className="mt-1 text-muted-foreground">
                처음이라면 봇에게 <code className="text-[12px]">/chatid</code> 를 보내고, 나온 숫자를
                앱 주인에게 알려주세요. 연결되면 <code className="text-[12px]">/month</code> 로 이번 달
                현황도 볼 수 있어요.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

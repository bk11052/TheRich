"use client";

import { useEffect, useState } from "react";
import { MessageCircle } from "lucide-react";
import { toast } from "sonner";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getSharedMe, type SharedMe } from "@/lib/api";

/** partner 의 더보기: 본인 정보와 텔레그램 안내만. owner 의 관리 화면은 노출하지 않는다. */
export function PartnerMore() {
  const [me, setMe] = useState<SharedMe | null>(null);

  useEffect(() => {
    getSharedMe()
      .then(setMe)
      .catch(() => toast.error("내 정보를 불러오지 못했어요"));
  }, []);

  return (
    <div className="mx-auto grid w-full max-w-xl gap-5">
      <div className="grid gap-2">
        <h2 className="px-1 text-[13px] font-medium text-muted-foreground">내 정보</h2>
        <Card className="gap-0 p-4">
          {me === null ? (
            <Skeleton className="h-6 w-32" />
          ) : (
            <p className="text-[15px] font-medium">{me.name}</p>
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

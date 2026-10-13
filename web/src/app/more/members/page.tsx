"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";
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
import { createMember, getMembers, updateMember, type Member } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState("");
  const [chatId, setChatId] = useState("");

  const reload = useCallback(() => {
    setLoading(true);
    getMembers()
      .then(setMembers)
      .catch(() => toast.error("멤버를 불러오지 못했어요"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(reload, [reload]);

  async function rename(member: Member, next: string) {
    const trimmed = next.trim();
    if (!trimmed || trimmed === member.name) return;
    try {
      await updateMember(member.id, { name: trimmed });
      reload();
    } catch {
      toast.error("이름을 바꾸지 못했어요");
    }
  }

  async function add() {
    if (!name.trim()) return;
    try {
      await createMember({
        name: name.trim(),
        telegram_chat_id: chatId.trim() ? Number(chatId.trim()) : null,
      });
      setAdding(false);
      setName("");
      setChatId("");
      reload();
    } catch {
      toast.error("추가하지 못했어요. chat id 가 이미 등록돼 있을 수 있어요.");
    }
  }

  return (
    <div className="mx-auto grid w-full max-w-xl gap-4">
      <ManageHeader title="함께 쓰는 사람" />
      <p className="-mt-2 px-1 text-[13px] text-muted-foreground">
        데이트비용을 같이 기록하는 사람
      </p>

      {loading ? (
        <Skeleton className="h-28 w-full" />
      ) : (
        <div className="grid gap-2">
          {members.map((m) => (
            <Card key={m.id} className="gap-0 p-4">
              <div className="flex items-center gap-3">
                <Input
                  defaultValue={m.name}
                  onBlur={(e) => rename(m, e.target.value)}
                  className="h-8 border-0 px-0 text-[15px] font-medium shadow-none focus-visible:ring-0"
                />
                {m.is_self && (
                  <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                    나
                  </span>
                )}
              </div>

              <p className="mt-2 text-[12px] text-muted-foreground">
                {m.telegram_chat_id
                  ? `텔레그램 ${m.telegram_chat_id}`
                  : "텔레그램 미연결 — 봇에 /chatid 를 보내 등록하세요"}
              </p>
            </Card>
          ))}

          <Button variant="outline" onClick={() => setAdding(true)} className="justify-start">
            <Plus className="size-4" />
            사람 추가
          </Button>
        </div>
      )}

      <Dialog open={adding} onOpenChange={setAdding}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>사람 추가</DialogTitle>
          </DialogHeader>
          <div className="grid gap-3">
            <Input
              placeholder="이름"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Input
              placeholder="텔레그램 chat id (선택)"
              value={chatId}
              onChange={(e) => setChatId(e.target.value)}
              inputMode="numeric"
            />
            <p className="text-[12px] text-muted-foreground">
              상대가 봇에게 /chatid 를 보내면 나오는 숫자예요. 등록된 사람만 봇으로 기록할 수 있어요.
            </p>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAdding(false)}>
              취소
            </Button>
            <Button onClick={add}>추가</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

import { getMembers, type Member } from "@/lib/api";

/** 멤버는 거의 안 바뀌고 여러 화면에서 쓰이므로 모듈 레벨에 한 번만 받아둔다. */
let cache: Member[] | null = null;
let inflight: Promise<Member[]> | null = null;

export function invalidateMembers() {
  cache = null;
  inflight = null;
}

export function useMembers(): Map<number, Member> {
  const [members, setMembers] = useState<Member[]>(cache ?? []);

  useEffect(() => {
    if (cache) {
      setMembers(cache);
      return;
    }
    inflight ??= getMembers().catch(() => [] as Member[]);
    inflight.then((list) => {
      cache = list;
      setMembers(list);
    });
  }, []);

  return new Map(members.map((m) => [m.id, m]));
}

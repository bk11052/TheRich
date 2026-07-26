"use client";

import Link from "next/link";
import {
  Bell,
  ChevronRight,
  CreditCard,
  Filter,
  KeyRound,
  PiggyBank,
  Tags,
  type LucideIcon,
} from "lucide-react";
import { toast } from "sonner";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Item = {
  icon: LucideIcon;
  label: string;
  desc: string;
  href?: string;
  soon?: boolean;
};

const SECTIONS: { title: string; items: Item[] }[] = [
  {
    title: "관리",
    items: [
      { icon: PiggyBank, label: "예산 설정", desc: "카테고리별 월 예산", href: "/more/budgets" },
      { icon: Tags, label: "카테고리", desc: "지출·수입 분류 관리", href: "/more/categories" },
      { icon: Filter, label: "자동분류 규칙", desc: "가맹점 → 카테고리 규칙", href: "/more/rules" },
    ],
  },
  {
    title: "혜택 · 정책",
    items: [
      { icon: CreditCard, label: "카드 혜택", desc: "최적 카드 추천·실적 추적", href: "/more/cards" },
      { icon: KeyRound, label: "주택청약", desc: "납입·가점·일정 알림", soon: true },
      { icon: Bell, label: "맞춤 정책", desc: "나·가족 정책 매칭 알림", soon: true },
    ],
  },
];

export default function MorePage() {
  return (
    <div className="mx-auto grid w-full max-w-xl gap-5">
      {SECTIONS.map((section) => (
        <div key={section.title} className="grid gap-2">
          <h2 className="px-1 text-[13px] font-medium text-muted-foreground">
            {section.title}
          </h2>
          <Card className="gap-0 overflow-hidden py-0">
            {section.items.map((it) => {
              const Icon = it.icon;
              const inner = (
                <>
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <Icon className="size-[18px]" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{it.label}</p>
                    <p className="truncate text-[12px] text-muted-foreground">{it.desc}</p>
                  </div>
                  {it.soon ? (
                    <span className="rounded-full border px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                      예정
                    </span>
                  ) : (
                    <ChevronRight className="size-4 text-muted-foreground" />
                  )}
                </>
              );
              const rowClass =
                "flex w-full items-center gap-3 border-b px-4 py-3 text-left last:border-b-0";

              if (it.href) {
                return (
                  <Link
                    key={it.label}
                    href={it.href}
                    className={cn(rowClass, "transition-colors hover:bg-accent")}
                  >
                    {inner}
                  </Link>
                );
              }
              return (
                <button
                  key={it.label}
                  type="button"
                  disabled={it.soon}
                  onClick={() => toast(`${it.label} 화면은 곧 추가돼요`)}
                  className={cn(rowClass, it.soon ? "opacity-55" : "transition-colors hover:bg-accent")}
                >
                  {inner}
                </button>
              );
            })}
          </Card>
        </div>
      ))}

      <p className="px-1 text-center text-[11px] text-muted-foreground/60">
        TheRich · Phase 1 (순자산 + 가계부)
      </p>
    </div>
  );
}

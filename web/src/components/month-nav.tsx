"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { addMonth, isFutureMonth, monthLabel } from "@/lib/month";
import { cn } from "@/lib/utils";

export function MonthNav({
  month,
  onChange,
  className,
}: {
  month: string;
  onChange: (month: string) => void;
  className?: string;
}) {
  const nextDisabled = isFutureMonth(addMonth(month, 1));
  return (
    <div className={cn("flex items-center justify-between", className)}>
      <button
        type="button"
        onClick={() => onChange(addMonth(month, -1))}
        aria-label="이전 달"
        className="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <ChevronLeft className="size-5" />
      </button>
      <span className="text-[15px] font-semibold tracking-tight tabular-nums">
        {monthLabel(month)}
      </span>
      <button
        type="button"
        disabled={nextDisabled}
        onClick={() => onChange(addMonth(month, 1))}
        aria-label="다음 달"
        className="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-30 disabled:hover:bg-transparent"
      >
        <ChevronRight className="size-5" />
      </button>
    </div>
  );
}

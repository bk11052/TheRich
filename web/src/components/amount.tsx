import { formatKRW, formatManwon } from "@/lib/format";
import { cn } from "@/lib/utils";

/**
 * 금액 표시 — 프라이버시 블러 대상.
 * body.privacy-on 이면 [data-private] 규칙으로 흐려진다(globals.css).
 */
export function Amount({
  value,
  compact = false,
  sign = false,
  className,
  private: isPrivate = true,
}: {
  value: number;
  compact?: boolean;
  sign?: boolean;
  className?: string;
  private?: boolean;
}) {
  const prefix = sign && value > 0 ? "+" : "";
  const text = compact ? formatManwon(value) : formatKRW(value);
  return (
    <span
      {...(isPrivate ? { "data-private": "" } : {})}
      className={cn("tabular-nums", className)}
    >
      {prefix}
      {text}
    </span>
  );
}

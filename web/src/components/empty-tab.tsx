import type { LucideIcon } from "lucide-react";

export function EmptyTab({
  icon: Icon,
  title,
  description,
  phase,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  phase?: string;
}) {
  return (
    <div className="flex min-h-[60dvh] flex-col items-center justify-center px-6 text-center">
      <span className="flex size-16 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        <Icon className="size-7" />
      </span>
      <h1 className="mt-4 text-lg font-semibold tracking-tight">{title}</h1>
      <p className="mt-1.5 max-w-xs text-sm text-muted-foreground">{description}</p>
      {phase && (
        <span className="mt-4 rounded-full border px-3 py-1 text-[11px] font-medium text-muted-foreground">
          {phase}
        </span>
      )}
    </div>
  );
}

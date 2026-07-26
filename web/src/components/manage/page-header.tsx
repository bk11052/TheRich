import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export function ManageHeader({
  title,
  action,
}: {
  title: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex items-center gap-1">
      <Link
        href="/more"
        aria-label="더보기로"
        className="-ml-2 inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <ChevronLeft className="size-5" />
      </Link>
      <h1 className="flex-1 text-lg font-semibold tracking-tight">{title}</h1>
      {action}
    </div>
  );
}

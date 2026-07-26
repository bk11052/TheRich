"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Camera, Eye, EyeOff, Home, Landmark, Menu, Wallet } from "lucide-react";

import { cn } from "@/lib/utils";
import { useBlur } from "@/components/providers/blur-provider";

const TABS = [
  { href: "/", label: "홈", icon: Home },
  { href: "/spending", label: "지출", icon: Wallet },
  { href: "/assets", label: "자산", icon: Landmark },
  { href: "/records", label: "기록", icon: Camera },
  { href: "/more", label: "더보기", icon: Menu },
] as const;

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

function BlurToggle({ withLabel = false }: { withLabel?: boolean }) {
  const { blurred, toggle } = useBlur();
  const Icon = blurred ? EyeOff : Eye;
  if (withLabel) {
    return (
      <button
        type="button"
        onClick={toggle}
        aria-pressed={blurred}
        className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <Icon className="size-[18px]" />
        {blurred ? "금액 보기" : "금액 가리기"}
      </button>
    );
  }
  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={blurred}
      aria-label={blurred ? "금액 보기" : "금액 가리기"}
      className="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
    >
      <Icon className="size-[18px]" />
    </button>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-dvh lg:mx-auto lg:flex lg:max-w-6xl">
      {/* 데스크톱 사이드바 */}
      <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col border-r px-3 py-5 lg:flex">
        <Link href="/" className="px-3 pb-6 text-[19px] font-semibold tracking-tight">
          TheRich
        </Link>
        <nav className="flex flex-1 flex-col gap-1">
          {TABS.map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-brand/10 text-brand"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
              >
                <Icon className="size-[18px]" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t pt-2">
          <BlurToggle withLabel />
        </div>
      </aside>

      {/* 컨텐츠 컬럼 */}
      <div className="flex min-h-dvh w-full flex-col lg:min-w-0 lg:flex-1">
        {/* 모바일 헤더 */}
        <header className="glass sticky top-0 z-30 flex h-14 items-center justify-between border-b px-4 lg:hidden">
          <Link href="/" className="text-[17px] font-semibold tracking-tight">
            TheRich
          </Link>
          <BlurToggle />
        </header>

        <main className="mx-auto w-full max-w-md flex-1 px-4 pb-28 pt-4 lg:max-w-none lg:px-8 lg:pb-12 lg:pt-8">
          {children}
        </main>

        {/* 모바일 하단 탭 */}
        <nav className="glass safe-bottom fixed inset-x-0 bottom-0 z-30 mx-auto flex w-full max-w-md items-stretch border-t px-2 pt-1.5 lg:hidden">
          {TABS.map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex flex-1 flex-col items-center gap-1 rounded-lg py-1 text-[10px] font-medium transition-colors",
                  active ? "text-brand" : "text-muted-foreground hover:text-foreground",
                )}
              >
                <Icon className={cn("size-[22px]", active && "stroke-[2.25]")} />
                {label}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}

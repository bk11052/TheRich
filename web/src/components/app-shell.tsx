"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Camera,
  Eye,
  EyeOff,
  Heart,
  Home,
  Landmark,
  LogOut,
  Menu,
  Wallet,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/components/providers/auth-provider";
import { useBlur } from "@/components/providers/blur-provider";
import { canAccess, homeFor, type Role } from "@/lib/roles";

// 데이트비용·기록 두 탭은 owner 와 partner 가 같은 화면을 본다. 나란히 둬서 묶음으로 읽히게.
const OWNER_TABS = [
  { href: "/", label: "홈", icon: Home },
  { href: "/spending", label: "지출", icon: Wallet },
  { href: "/assets", label: "자산", icon: Landmark },
  { href: "/shared", label: "데이트비용", icon: Heart },
  { href: "/records", label: "기록", icon: Camera },
  { href: "/more", label: "더보기", icon: Menu },
] as const;

// partner 는 공유 예산·우리 기록·자기 설정만 본다. 서버가 나머지를 403 으로 막으므로
// 여기 목록은 "안 보이게" 하는 편의이지 보안 장치가 아니다.
const PARTNER_TABS = [
  { href: "/shared", label: "데이트비용", icon: Heart },
  { href: "/records", label: "기록", icon: Camera },
  { href: "/more", label: "더보기", icon: Menu },
] as const;

function tabsFor(role: Role) {
  return role === "partner" ? PARTNER_TABS : OWNER_TABS;
}

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

function SignOutButton({ withLabel = false }: { withLabel?: boolean }) {
  const { signOut } = useAuth();
  if (withLabel) {
    return (
      <button
        type="button"
        onClick={signOut}
        className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <LogOut className="size-[18px]" />
        로그아웃
      </button>
    );
  }
  // 모바일에는 사이드바가 없으므로 헤더에도 둔다. 없으면 로그아웃할 방법이 사라진다.
  return (
    <button
      type="button"
      onClick={signOut}
      aria-label="로그아웃"
      className="inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
    >
      <LogOut className="size-[18px]" />
    </button>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { loading, status } = useAuth();
  const authed = status?.authenticated === true;
  const role: Role = authed ? status.role : "owner";

  useEffect(() => {
    if (loading) return;
    if (!authed) {
      if (pathname !== "/login") router.replace("/login");
      return;
    }
    // 역할에 없는 경로로 들어오면 각자의 첫 화면으로. 서버도 403 을 내지만
    // 빈 화면 대신 갈 곳을 보여주는 게 낫다.
    if (!canAccess(status.role, pathname)) router.replace(homeFor(status.role));
  }, [loading, authed, status, pathname, router]);

  // 첫 조회 중에는 아무것도 그리지 않는다 — 로그인 화면이 깜빡였다 사라지는 걸 막는다.
  if (loading) {
    return <div className="min-h-dvh" aria-busy="true" />;
  }

  // 로그인 화면은 네비게이션 없이 단독으로.
  if (!authed) {
    return <div className="min-h-dvh">{pathname === "/login" ? children : null}</div>;
  }

  const TABS = tabsFor(role);
  const home = homeFor(role);
  // 위 useEffect 가 리다이렉트하는 동안 본문을 그리지 않는다. 그리면 해당 페이지가
  // 자기 데이터를 먼저 요청해 403 을 줄줄이 내고, 스켈레톤이 잠깐 비친다.
  const allowed = canAccess(role, pathname);

  return (
    <div className="min-h-dvh lg:mx-auto lg:flex lg:max-w-6xl">
      {/* 데스크톱 사이드바 */}
      <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col border-r px-3 py-5 lg:flex">
        <Link href={home} className="px-3 pb-6 text-[19px] font-semibold tracking-tight">
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
        <div className="grid border-t pt-2">
          <BlurToggle withLabel />
          <SignOutButton withLabel />
        </div>
      </aside>

      {/* 컨텐츠 컬럼 */}
      <div className="flex min-h-dvh w-full flex-col lg:min-w-0 lg:flex-1">
        {/* 모바일 헤더 */}
        <header className="glass sticky top-0 z-30 flex h-14 items-center justify-between border-b px-4 lg:hidden">
          <Link href={home} className="text-[17px] font-semibold tracking-tight">
            TheRich
          </Link>
          <div className="flex items-center">
            <BlurToggle />
            <SignOutButton />
          </div>
        </header>

        <main className="mx-auto w-full max-w-md flex-1 px-4 pb-28 pt-4 lg:max-w-none lg:px-8 lg:pb-12 lg:pt-8">
          {allowed ? children : null}
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

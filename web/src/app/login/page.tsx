"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, Eye, EyeOff, Loader2 } from "lucide-react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, login } from "@/lib/api";
import { homeFor } from "@/lib/roles";
import { cn } from "@/lib/utils";

// 이름은 비밀이 아니고 매번 치기 번거로우니 기기에 기억해 둔다. 비밀번호는 절대 저장하지 않는다
// — 그건 브라우저/키체인의 몫이고, 아래 autoComplete 속성이 그쪽에 신호를 준다.
const LAST_NAME_KEY = "therich:last-login-name";

function readLastName(): string {
  try {
    return localStorage.getItem(LAST_NAME_KEY) ?? "";
  } catch {
    return "";
  }
}

function saveLastName(name: string) {
  try {
    localStorage.setItem(LAST_NAME_KEY, name);
  } catch {
    // 사파리 개인정보 보호 모드 등에서는 저장이 막힌다. 기억 못 해도 로그인엔 지장 없음.
  }
}

/** 서버가 준 detail 을 우선 쓰고, 없으면 상태코드로 문장을 고른다. */
function messageFor(err: unknown): string {
  if (!(err instanceof ApiError)) {
    return "서버에 연결할 수 없어요. 백엔드가 켜져 있는지 확인해 주세요.";
  }
  let detail = "";
  try {
    detail = JSON.parse(err.body)?.detail ?? "";
  } catch {
    // 본문이 JSON 이 아니면 기본 문구로.
  }
  if (err.status === 429) return detail || "시도가 너무 많아요. 잠시 뒤에 다시 해 주세요.";
  if (err.status === 401) return "이름 또는 비밀번호가 올바르지 않아요.";
  return "로그인하지 못했어요. 잠시 뒤에 다시 시도해 주세요.";
}

export default function LoginPage() {
  const router = useRouter();
  const { status, refresh } = useAuth();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [capsLock, setCapsLock] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  // 이미 로그인된 채로 /login 에 들어오면 각자의 첫 화면으로.
  useEffect(() => {
    if (status?.authenticated) router.replace(homeFor(status.role));
  }, [status, router]);

  // 지난번 이름이 있으면 채우고 바로 비밀번호 칸으로 — 대부분 이름은 매번 같다.
  useEffect(() => {
    const last = readLastName();
    if (last) {
      setName(last);
      passwordRef.current?.focus();
    } else {
      nameRef.current?.focus();
    }
  }, []);

  // 보기 토글로 type 이 password→text 로 바뀌면 커서가 맨 앞으로 튄다. 그대로 두면
  // "abc" 입력 → 보기 → "123" 입력이 "123abc" 가 된다.
  // 실측: 커서는 JS 호출 없이 다음 레이아웃 계산 때 브라우저가 0 으로 되돌린다. 그래서
  // 레이아웃을 먼저 강제로 일으켜 그 리셋을 지금 끝내 버린 뒤 끝으로 옮긴다.
  // 다음 프레임 보정은 그래도 어긋나는 브라우저를 위한 안전망.
  useLayoutEffect(() => {
    const el = passwordRef.current;
    if (!el || document.activeElement !== el) return;
    const toEnd = () => {
      if (document.activeElement !== el) return;
      void el.offsetWidth; // 레이아웃 강제 — 브라우저의 커서 리셋을 여기서 먼저 일어나게 한다
      const end = el.value.length;
      el.setSelectionRange(end, end);
    };
    toEnd();
    const raf = requestAnimationFrame(toEnd);
    return () => cancelAnimationFrame(raf);
  }, [showPassword]);

  function trackCapsLock(e: React.KeyboardEvent<HTMLInputElement>) {
    setCapsLock(e.getModifierState?.("CapsLock") ?? false);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (busy || !trimmed || !password) return;
    setBusy(true);
    setError(null);
    try {
      await login(trimmed, password);
      saveLastName(trimmed);
      await refresh();
      // 성공하면 위 useEffect 가 역할에 맞는 화면으로 보낸다.
    } catch (err) {
      setError(messageFor(err));
      setBusy(false);
      // 틀린 건 거의 항상 비밀번호이므로 그 칸을 비우고 다시 입력하게 한다.
      setPassword("");
      passwordRef.current?.focus();
    }
  }

  const canSubmit = !busy && name.trim().length > 0 && password.length > 0;

  return (
    // 이미지 높이·제목 위치·페이드는 globals.css 의 .login-* 에서 한 묶음으로 관리한다.
    <div className="login-page relative min-h-dvh overflow-x-hidden pb-10">
      {/* 장식용 이미지 — 스크린리더가 읽을 정보가 없으므로 숨긴다. */}
      <div
        aria-hidden
        className="login-hero login-hero-mask pointer-events-none absolute inset-x-0 top-0 mx-auto w-full max-w-md select-none"
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- 정적 장식 이미지 하나라 최적화 파이프라인이 필요 없다 */}
        <img
          src="/images/login-hero.webp"
          alt=""
          width={900}
          height={1080}
          fetchPriority="high"
          decoding="async"
          className="size-full object-cover object-[50%_15%]"
        />
      </div>

      <div className="login-content relative mx-auto w-full max-w-sm px-4">
        <div className="mb-7 text-center">
          <h1 className="login-wordmark text-[46px] leading-none font-bold tracking-[-0.035em]">
            TheRich
          </h1>
        </div>

        {/* method/action 과 name 속성은 iCloud 키체인 등 비밀번호 관리자가 폼을 알아보게 하는 신호다. */}
        <form
          onSubmit={submit}
          method="post"
          action="#"
          noValidate
          className="grid gap-4 rounded-2xl border bg-card p-6 shadow-sm"
        >
          <div className="grid gap-1.5">
            <label htmlFor="login-name" className="text-[13px] font-medium">
              이름
            </label>
            <Input
              ref={nameRef}
              id="login-name"
              name="username"
              autoComplete="username"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
              enterKeyHint="next"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError(null);
              }}
              className="h-11 text-[15px]"
            />
          </div>

          <div className="grid gap-1.5">
            <label htmlFor="login-password" className="text-[13px] font-medium">
              비밀번호
            </label>
            <div className="relative">
              <Input
                ref={passwordRef}
                id="login-password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                enterKeyHint="go"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError(null);
                }}
                onKeyDown={trackCapsLock}
                onKeyUp={trackCapsLock}
                onBlur={() => setCapsLock(false)}
                aria-invalid={error ? true : undefined}
                aria-describedby={
                  [capsLock && "login-caps", error && "login-error"].filter(Boolean).join(" ") ||
                  undefined
                }
                className="h-11 pr-11 text-[15px]"
              />
              <button
                type="button"
                // 마우스·터치로 누를 때 포커스를 입력칸에 남긴다. 안 그러면 폰에서는 키보드가
                // 내려가고, 데스크톱에서는 이어서 친 글자와 Enter 가 이 버튼으로 간다.
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
                aria-pressed={showPassword}
                className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-r-lg text-muted-foreground transition-colors hover:text-foreground"
              >
                {showPassword ? <EyeOff className="size-[18px]" /> : <Eye className="size-[18px]" />}
              </button>
            </div>
            {capsLock && (
              <p id="login-caps" className="text-[12px] text-amber-600 dark:text-amber-500">
                Caps Lock 이 켜져 있어요
              </p>
            )}
          </div>

          <div aria-live="polite" className={cn(!error && "sr-only")}>
            {error && (
              <p
                id="login-error"
                role="alert"
                className="flex items-start gap-2 text-[13px] text-destructive"
              >
                <AlertCircle className="mt-px size-4 shrink-0" />
                {error}
              </p>
            )}
          </div>

          <Button type="submit" disabled={!canSubmit} className="h-11 text-[15px]">
            {busy ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                확인 중
              </>
            ) : (
              "로그인"
            )}
          </Button>
        </form>

        <p className="mt-6 text-center text-[12px] text-muted-foreground">
          계정이 없다면 앱 주인에게 만들어 달라고 해 주세요.
        </p>
      </div>
    </div>
  );
}

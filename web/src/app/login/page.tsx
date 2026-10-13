"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogIn } from "lucide-react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ApiError, login } from "@/lib/api";
import { homeFor } from "@/lib/roles";

export default function LoginPage() {
  const router = useRouter();
  const { status, refresh } = useAuth();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // 이미 로그인된 채로 /login 에 들어오면 각자의 첫 화면으로 보낸다.
  useEffect(() => {
    if (status?.authenticated) router.replace(homeFor(status.role));
  }, [status, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await login(name.trim(), password);
      await refresh();
    } catch (err) {
      setError(
        err instanceof ApiError && err.isUnauthenticated
          ? "이름 또는 비밀번호가 올바르지 않아요."
          : "로그인할 수 없어요. 서버가 켜져 있는지 확인해 주세요.",
      );
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center px-4">
      <Card className="w-full max-w-sm gap-0 p-6">
        <h1 className="text-[22px] font-semibold tracking-tight">TheRich</h1>
        <p className="mt-1 text-[13px] text-muted-foreground">
          계속하려면 로그인하세요.
        </p>

        <form onSubmit={submit} className="mt-6 grid gap-3">
          <Input
            placeholder="이름"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="username"
            autoFocus
          />
          <Input
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          {error && (
            <p role="alert" className="text-[13px] text-destructive">
              {error}
            </p>
          )}
          <Button type="submit" disabled={busy || !name.trim() || !password}>
            <LogIn className="size-4" />
            {busy ? "확인 중…" : "로그인"}
          </Button>
        </form>

        <p className="mt-5 text-[12px] leading-relaxed text-muted-foreground">
          계정은 터미널에서 만듭니다.
          <br />
          <code className="text-[11px]">python -m app.manage add-partner &lt;이름&gt;</code>
        </p>
      </Card>
    </div>
  );
}

"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

type BlurContextValue = {
  blurred: boolean;
  toggle: () => void;
};

const BlurContext = createContext<BlurContextValue | null>(null);

const STORAGE_KEY = "therich:privacy-blur";

export function BlurProvider({ children }: { children: React.ReactNode }) {
  // 기본 ON(가림) — 메모의 UX 결정(기본 ON, 집 와이파이 자동 OFF는 후속)
  const [blurred, setBlurred] = useState(true);

  // 초기 마운트 시 저장된 값 복원
  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved !== null) setBlurred(saved === "1");
  }, []);

  // body 클래스 동기화
  useEffect(() => {
    document.body.classList.toggle("privacy-on", blurred);
    window.localStorage.setItem(STORAGE_KEY, blurred ? "1" : "0");
  }, [blurred]);

  const toggle = useCallback(() => setBlurred((v) => !v), []);

  return (
    <BlurContext.Provider value={{ blurred, toggle }}>{children}</BlurContext.Provider>
  );
}

export function useBlur() {
  const ctx = useContext(BlurContext);
  if (!ctx) throw new Error("useBlur must be used within BlurProvider");
  return ctx;
}

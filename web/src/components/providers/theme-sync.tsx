"use client";

import { useEffect } from "react";

const QUERY = "(prefers-color-scheme: dark)";

/**
 * 시스템 다크모드를 <html class="dark"> 에 계속 반영한다.
 *
 * layout 의 인라인 스크립트는 첫 페인트 전에 한 번만 판단해서 깜빡임을 막는다.
 * 그 이후는 아무도 안 봤기 때문에, 라이트일 때 열어 둔 탭은 시스템이 다크로 바뀌어도
 * (macOS 자동 전환 등) 계속 흰 화면이었다. 여기서 변경을 구독해 따라간다.
 * 마운트 때도 한 번 다시 적용해, 개발 중 HMR 로 html className 이 다시 쓰여도 복구된다.
 */
export function ThemeSync() {
  useEffect(() => {
    const media = window.matchMedia(QUERY);
    const apply = () => document.documentElement.classList.toggle("dark", media.matches);
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, []);
  return null;
}

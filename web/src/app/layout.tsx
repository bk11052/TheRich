import type { Metadata, Viewport } from "next";
import "./globals.css";

import { AppShell } from "@/components/app-shell";
import { BlurProvider } from "@/components/providers/blur-provider";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "TheRich",
  description: "개인 자산관리 대시보드 — 순자산 · 가계부",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "TheRich" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
  ],
};

// 시스템 다크모드 반영 (FOUC 방지용 블로킹 스크립트)
const themeScript = `(function(){try{var d=window.matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.classList.toggle('dark',d);}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-full">
        <BlurProvider>
          <AppShell>{children}</AppShell>
          <Toaster position="top-center" />
        </BlurProvider>
      </body>
    </html>
  );
}

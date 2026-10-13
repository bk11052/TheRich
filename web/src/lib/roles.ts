/** 역할별로 접근 가능한 경로와 첫 화면. 화면 가리기는 편의일 뿐, 실제 차단은 서버가 한다. */

export type Role = "owner" | "partner";

// partner 가 들어갈 수 있는 경로.
// /shared, /records 는 하위까지 허용. /more 는 **그 페이지만** — /more/budgets 같은
// 하위 관리 화면은 owner 의 예산·카드·가계부 설정이라 막는다.
const PARTNER_PREFIXES = ["/shared", "/records"];
const PARTNER_EXACT = ["/more"];

export function homeFor(role: Role): string {
  return role === "partner" ? "/shared" : "/";
}

export function canAccess(role: Role, pathname: string): boolean {
  if (role === "owner") return true;
  if (PARTNER_EXACT.includes(pathname)) return true;
  return PARTNER_PREFIXES.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

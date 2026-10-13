/** 역할별로 접근 가능한 경로와 첫 화면. 화면 가리기는 편의일 뿐, 실제 차단은 서버가 한다. */

export type Role = "owner" | "partner";

/** partner 가 들어갈 수 있는 경로. 그 외는 전부 /shared 로 돌려보낸다. */
const PARTNER_PATHS = ["/shared"];

export function homeFor(role: Role): string {
  return role === "partner" ? "/shared" : "/";
}

export function canAccess(role: Role, pathname: string): boolean {
  if (role === "owner") return true;
  return PARTNER_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"));
}

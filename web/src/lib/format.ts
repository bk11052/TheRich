/** 금액은 항상 원(정수). 표시용 포맷 헬퍼. */

export function formatKRW(amount: number): string {
  return "₩" + Math.round(amount).toLocaleString("ko-KR");
}

/** 큰 금액 축약: 1,234,000 → "123.4만", 12,000 → "1.2만", 900 → "900" */
export function formatManwon(amount: number): string {
  const abs = Math.abs(amount);
  const sign = amount < 0 ? "-" : "";
  if (abs >= 100_000_000) return `${sign}${(abs / 100_000_000).toFixed(1)}억`;
  if (abs >= 10_000) {
    const man = abs / 10_000;
    return `${sign}${man >= 100 ? Math.round(man) : man.toFixed(1)}만`;
  }
  return `${sign}${abs.toLocaleString("ko-KR")}`;
}

export function formatPercent(ratio: number, digits = 0): string {
  return `${(ratio * 100).toFixed(digits)}%`;
}

/** "YYYY-MM" 월 문자열 유틸. */

export function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function parseMonth(month: string): { year: number; month: number } {
  const [y, m] = month.split("-").map(Number);
  return { year: y, month: m };
}

export function addMonth(month: string, delta: number): string {
  const { year, month: m } = parseMonth(month);
  const d = new Date(year, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function monthLabel(month: string): string {
  const { year, month: m } = parseMonth(month);
  return `${year}년 ${m}월`;
}

export function daysInMonth(month: string): number {
  const { year, month: m } = parseMonth(month);
  return new Date(year, m, 0).getDate();
}

/** 해당 월 1일의 요일 (0=일 ~ 6=토) */
export function firstWeekday(month: string): number {
  const { year, month: m } = parseMonth(month);
  return new Date(year, m - 1, 1).getDay();
}

/** ISO 날짜문자열 → 일(day of month) */
export function dayOf(iso: string): number {
  return new Date(iso).getDate();
}

export function isFutureMonth(month: string): boolean {
  return month > currentMonth();
}

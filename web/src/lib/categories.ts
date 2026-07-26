/**
 * 카테고리 시각화 매핑.
 * 백엔드 category.icon 은 이모지로 저장돼 있으나 UI 규칙상 이모지 금지 →
 * 여기서 이름 기준으로 Lucide 아이콘에 매핑해 렌더한다.
 */
import {
  Banknote,
  Bike,
  BookOpen,
  Bus,
  CircleDollarSign,
  Clapperboard,
  Coffee,
  Coins,
  Gift,
  House,
  Landmark,
  Pill,
  Plane,
  Plus,
  ReceiptText,
  Repeat,
  RotateCcw,
  ShieldCheck,
  Shirt,
  ShoppingBag,
  ShoppingCart,
  Smartphone,
  Store,
  Tag,
  TrendingUp,
  Utensils,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  식비: Utensils,
  배달: Bike,
  "카페/간식": Coffee,
  편의점: Store,
  "마트/장보기": ShoppingCart,
  교통: Bus,
  통신: Smartphone,
  "주거/월세": House,
  "관리비/공과금": ReceiptText,
  구독: Repeat,
  보험: ShieldCheck,
  쇼핑: ShoppingBag,
  "의류/미용": Shirt,
  "의료/건강": Pill,
  "문화/여가": Clapperboard,
  여행: Plane,
  교육: BookOpen,
  경조사: Gift,
  "세금/수수료": Landmark,
  기타지출: Tag,
  급여: Banknote,
  용돈: Coins,
  "이자/배당": TrendingUp,
  "환급/캐시백": RotateCcw,
  기타수입: Plus,
};

export function categoryIcon(name: string | undefined | null): LucideIcon {
  if (!name) return CircleDollarSign;
  return ICONS[name] ?? CircleDollarSign;
}

/** 도넛/차트용 색상 — CSS 변수 --chart-1..8 순환 */
export function chartColor(index: number): string {
  return `var(--chart-${(index % 8) + 1})`;
}

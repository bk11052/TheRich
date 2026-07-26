import { Camera } from "lucide-react";

import { EmptyTab } from "@/components/empty-tab";

export default function RecordsPage() {
  return (
    <EmptyTab
      icon={Camera}
      title="기록"
      description="지출에 장소·음식 사진·태그를 붙여 맛집/추억으로 남깁니다. 갤러리·지도 뷰가 들어올 자리예요."
      phase="Phase 3 · 자리만"
    />
  );
}

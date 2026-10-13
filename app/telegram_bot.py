"""TheRich 텔레그램 봇 (별도 프로세스) — **데이트비용 전용 창구**.

둘이 각자 1:1 대화로 지출을 올리면 공유 카테고리(Category.is_shared)에 저장되고,
저장 직후 이번 달 한도 대비 잔액을 돌려준다. 개인 지출은 웹에서 입력한다.

**등록된 chat_id 만 받는다.** 텔레그램 봇은 username 만 알면 누구나 말을 걸 수 있어서,
허용목록이 없으면 아무나 가계부에 거래를 쓸 수 있다. 허용목록 = Member.telegram_chat_id.

실행:
  1) @BotFather 에서 봇 생성 → 토큰을 .env 의 TELEGRAM_BOT_TOKEN 에 넣기
  2) 백엔드 먼저 실행:  uvicorn app.main:app
  3) 봇 실행:          python -m app.telegram_bot
  4) 각자 봇에게 /chatid → 나온 id 를 POST /members 로 등록
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import settings
from app.services import ocr
from app.services.expense_parser import ParsedExpense, parse_expense, parse_receipt
from app.services.members import normalize_color
from app.services.shared_budget import format_status_message

API = settings.api_base_url.rstrip("/")
KST = ZoneInfo("Asia/Seoul")
_cat_cache: dict[int, str] = {}


# ---------- 백엔드 API 헬퍼 ----------
async def _get(path: str):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{API}{path}")
        r.raise_for_status()
        return r.json()


async def _post(path: str, json: dict):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{API}{path}", json=json)
        r.raise_for_status()
        return r.json()


async def _resolve_member(chat_id: int) -> dict | None:
    """등록된 활성 멤버만. 봇 허용목록."""
    try:
        for m in await _get("/members"):
            if m.get("telegram_chat_id") == chat_id:
                return m
    except httpx.HTTPError:
        return None
    return None


async def _shared_category_id() -> int | None:
    for c in await _get("/categories"):
        if c.get("is_shared"):
            return c["id"]
    return None


async def _status_text(saved: str | None = None) -> str:
    month = datetime.now(KST).strftime("%Y-%m")
    try:
        status = await _get(f"/shared/budget?month={month}")
    except httpx.HTTPStatusError:
        status = None  # 404 = 공유 예산 미설정
    return format_status_message(status, saved=saved)


async def _deny(update: Update) -> None:
    await update.message.reply_text(
        "등록되지 않은 사용자예요.\n"
        f"이 채팅 id 는 {update.effective_chat.id} 입니다. "
        "앱 주인에게 전달해 등록을 요청해 주세요."
    )


async def _resolve_account_id() -> int | None:
    if settings.telegram_default_account_id:
        return settings.telegram_default_account_id
    accounts = await _get("/accounts")
    active = [a for a in accounts if not a["archived"]]
    if not active:
        return None
    cards = [a for a in active if a["type"] == "card"]
    return (cards or active)[0]["id"]


async def _category_name(cat_id: int | None) -> str:
    if cat_id is None:
        return "미분류"
    if not _cat_cache:
        for c in await _get("/categories"):
            _cat_cache[c["id"]] = c["name"]
    return _cat_cache.get(cat_id, "미분류")


# ---------- 핸들러 ----------
async def start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    member = await _resolve_member(update.effective_chat.id)
    if member is None:
        await _deny(update)
        return
    await update.message.reply_text(
        f"{member['name']}님, TheRich 데이트비용 봇이에요.\n\n"
        "데이트비용은 '가맹점 금액' 형식으로 보내면 저장돼요.\n"
        "  예) 스타벅스 5500\n"
        "영수증 사진을 보내도 읽어드려요.\n\n"
        "/date  이번 달 현황\n"
        "/color  내 색 바꾸기 (예: /color 파랑)\n"
        "/chatid  이 채팅 id"
    )


async def chatid(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"이 채팅 id: {update.effective_chat.id}\n"
        "앱 주인에게 전달하면 멤버로 등록해 줍니다."
    )


async def date_cmd(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if await _resolve_member(update.effective_chat.id) is None:
        await _deny(update)
        return
    try:
        await update.message.reply_text(await _status_text())
    except httpx.HTTPError:
        await update.message.reply_text("백엔드에 연결할 수 없어요. 서버가 켜져 있나요?")


async def color_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    member = await _resolve_member(update.effective_chat.id)
    if member is None:
        await _deny(update)
        return
    raw = " ".join(ctx.args) if ctx.args else ""
    color = normalize_color(raw)
    if color is None:
        await update.message.reply_text(
            f"지금 내 색: {member.get('color') or '없음'}\n"
            "바꾸려면 색 이름이나 hex 를 붙여주세요.\n"
            "  예) /color 파랑   /color #ff8800"
        )
        return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.patch(f"{API}/members/{member['id']}", json={"color": color})
            r.raise_for_status()
    except httpx.HTTPError:
        await update.message.reply_text("색 변경 실패 — 백엔드에 연결할 수 없어요.")
        return
    await update.message.reply_text(f"내 색을 {color} 로 바꿨어요.")


async def _ask_confirm(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE, parsed: ParsedExpense, prefix: str = ""
) -> None:
    ctx.user_data["pending"] = {"amount": parsed.amount, "merchant": parsed.merchant}
    kb = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("저장", callback_data="confirm"),
            InlineKeyboardButton("취소", callback_data="cancel"),
        ]]
    )
    merch = parsed.merchant or "(미상)"
    await update.message.reply_text(
        f"{prefix}{merch} · {parsed.amount:,}원\n데이트비용으로 저장할까요?", reply_markup=kb
    )


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if await _resolve_member(update.effective_chat.id) is None:
        await _deny(update)
        return
    parsed = parse_expense(update.message.text)
    if not parsed:
        await update.message.reply_text(
            "금액을 못 찾았어요. '가맹점 금액' 형식으로 보내주세요. 예: 스타벅스 5500"
        )
        return
    await _ask_confirm(update, ctx, parsed)


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    member = await _resolve_member(q.message.chat.id)
    if member is None:
        await q.edit_message_text("등록되지 않은 사용자예요.")
        return
    pending = ctx.user_data.pop("pending", None)
    if q.data == "cancel" or not pending:
        await q.edit_message_text("취소했어요.")
        return
    try:
        account_id = await _resolve_account_id()
        if account_id is None:
            await q.edit_message_text("계좌가 없어요. 앱에서 계좌를 먼저 추가해주세요.")
            return
        category_id = await _shared_category_id()
        if category_id is None:
            await q.edit_message_text(
                "공유 카테고리가 없어요. 앱에서 '데이트' 카테고리를 만들고 "
                "공유로 표시해 주세요."
            )
            return
        await _post(
            "/transactions",
            {
                "account_id": account_id,
                "type": "expense",
                "amount": pending["amount"],
                "occurred_at": datetime.now(KST).replace(tzinfo=None).isoformat(),
                "merchant": pending["merchant"],
                "source": "telegram_ocr",
                "category_id": category_id,   # 봇은 데이트비용 전용 — 규칙엔진 우회
                "payer_id": member["id"],
            },
        )
    except httpx.HTTPError:
        await q.edit_message_text("저장 실패 — 백엔드에 연결할 수 없어요.")
        return

    merch = pending["merchant"] or "(미상)"
    saved = f"{merch} {pending['amount']:,}원 · {member['name']}"
    try:
        await q.edit_message_text(await _status_text(saved=saved))
    except httpx.HTTPError:
        await q.edit_message_text(f"기록했어요 — {saved}")


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if await _resolve_member(update.effective_chat.id) is None:
        await _deny(update)
        return
    if not ocr.is_available():
        await update.message.reply_text(
            "이 서버에선 사진 OCR을 쓸 수 없어요(맥 로컬 전용). '가맹점 금액' 텍스트로 보내주세요."
        )
        return
    await update.message.reply_text("사진 읽는 중…")
    tg_file = await update.message.photo[-1].get_file()
    raw = await tg_file.download_as_bytearray()
    text = ocr.extract_text(bytes(raw))
    parsed = parse_receipt(text)
    if not parsed:
        await update.message.reply_text(
            "사진에서 금액을 못 읽었어요. '가맹점 금액' 텍스트로 보내주세요."
        )
        return
    await _ask_confirm(update, ctx, parsed, prefix="사진에서 읽었어요\n")


async def nudge(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """등록된 모든 멤버에게 전날 데이트비용 입력을 묻는다."""
    try:
        members = await _get("/members")
    except httpx.HTTPError:
        return
    for m in members:
        chat_id = m.get("telegram_chat_id")
        if not chat_id:
            continue
        await ctx.bot.send_message(
            chat_id=chat_id,
            text="어제 쓴 데이트비용 있나요? 내역을 보내주세요. 예: 스타벅스 5500",
        )


async def summary_job(ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """정기 요약 — 등록된 모든 멤버에게 이번 달 현황을 보낸다."""
    try:
        text = await _status_text()
        members = await _get("/members")
    except httpx.HTTPError:
        return
    for m in members:
        if m.get("telegram_chat_id"):
            await ctx.bot.send_message(chat_id=m["telegram_chat_id"], text=text)


def main() -> None:
    if not settings.telegram_bot_token:
        print(
            "TELEGRAM_BOT_TOKEN 이 없어요.\n"
            "  1) 텔레그램에서 @BotFather → /newbot 으로 봇 생성\n"
            "  2) 발급된 토큰을 .env 의 TELEGRAM_BOT_TOKEN 에 넣기\n"
            "  3) 다시 python -m app.telegram_bot 실행"
        )
        return

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CommandHandler("date", date_cmd))
    app.add_handler(CommandHandler("color", color_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    if app.job_queue:
        # 수신자는 .env 가 아니라 DB 의 멤버 목록에서 그때그때 읽는다.
        app.job_queue.run_daily(nudge, time=time(hour=0, minute=30, tzinfo=KST))
        # 주간 요약: 매주 월요일 오전 9시 / 월간 요약: 매월 1일 오전 9시
        app.job_queue.run_daily(
            summary_job, time=time(hour=9, tzinfo=KST), days=(0,)
        )
        app.job_queue.run_monthly(summary_job, when=time(hour=9, tzinfo=KST), day=1)
        print("넛지(00:30) · 주간요약(월 09:00) · 월간요약(1일 09:00) 활성화")

    print(f"봇 시작 — 데이트비용 전용. 백엔드 {API}. Ctrl+C 로 종료.")
    app.run_polling()


if __name__ == "__main__":
    main()

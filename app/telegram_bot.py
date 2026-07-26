"""TheRich 텔레그램 봇 (별도 프로세스).

역할: 모바일 지출 입력 창구. 텍스트로 '가맹점 금액'을 보내면 확인 후 백엔드
API(POST /transactions)로 저장한다. 자동분류(규칙엔진)는 백엔드가 처리.

실행:
  1) @BotFather 에서 봇 생성 → 토큰을 .env 의 TELEGRAM_BOT_TOKEN 에 넣기
  2) 백엔드 먼저 실행:  uvicorn app.main:app
  3) 봇 실행:          python -m app.telegram_bot
  4) 봇에게 /chatid → 나온 id 를 .env 의 TELEGRAM_CHAT_ID 에 넣으면 매일 00:30 넛지

사진 OCR 은 아직 스텁(텍스트 입력만). 로컬 OCR(Apple Vision/Tesseract)은 후속.
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
    await update.message.reply_text(
        "TheRich 가계부 봇이에요.\n\n"
        "지출은 '가맹점 금액' 형식으로 보내면 저장돼요.\n"
        "  예) 스타벅스 5500\n"
        "  예) 점심 김밥천국 8000\n\n"
        "/month  이번 달 요약\n"
        "/chatid  매일 넛지 설정용 chat id"
    )


async def chatid(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"이 채팅 id: {update.effective_chat.id}\n"
        ".env 의 TELEGRAM_CHAT_ID 에 넣으면 매일 00:30 넛지를 받아요."
    )


async def month_cmd(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    month = datetime.now(KST).strftime("%Y-%m")
    try:
        txns = await _get(f"/transactions?month={month}&limit=500")
    except httpx.HTTPError:
        await update.message.reply_text("백엔드에 연결할 수 없어요. 서버가 켜져 있나요?")
        return
    spent = sum(t["amount"] for t in txns if t["type"] == "expense")
    income = sum(t["amount"] for t in txns if t["type"] == "income")
    await update.message.reply_text(
        f"{month} 요약\n지출 {spent:,}원\n수입 {income:,}원\n건수 {len(txns)}건"
    )


async def _ask_confirm(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE, parsed: ParsedExpense, prefix: str = ""
) -> None:
    ctx.user_data["pending"] = {"amount": parsed.amount, "merchant": parsed.merchant}
    kb = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ 저장", callback_data="confirm"),
            InlineKeyboardButton("취소", callback_data="cancel"),
        ]]
    )
    merch = parsed.merchant or "(미상)"
    await update.message.reply_text(
        f"{prefix}{merch} · {parsed.amount:,}원\n지출로 저장할까요?", reply_markup=kb
    )


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
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
    pending = ctx.user_data.pop("pending", None)
    if q.data == "cancel" or not pending:
        await q.edit_message_text("취소했어요.")
        return
    try:
        account_id = await _resolve_account_id()
        if account_id is None:
            await q.edit_message_text("계좌가 없어요. 앱에서 계좌를 먼저 추가해주세요.")
            return
        txn = await _post(
            "/transactions",
            {
                "account_id": account_id,
                "type": "expense",
                "amount": pending["amount"],
                "occurred_at": datetime.now(KST).replace(tzinfo=None).isoformat(),
                "merchant": pending["merchant"],
                "source": "telegram_ocr",
            },
        )
    except httpx.HTTPError:
        await q.edit_message_text("저장 실패 — 백엔드에 연결할 수 없어요.")
        return
    cat = await _category_name(txn.get("category_id"))
    merch = pending["merchant"] or "(미상)"
    await q.edit_message_text(
        f"✅ 저장했어요\n{merch} · {pending['amount']:,}원 · {cat}"
    )


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
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
    await ctx.bot.send_message(
        chat_id=settings.telegram_chat_id,
        text="어제 쓴 지출 입력했나요? 내역을 보내주세요. 예: 스타벅스 5500",
    )


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
    app.add_handler(CommandHandler("month", month_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    # 매일 00:30(KST) 지출 넛지 (chat id 설정 시)
    if settings.telegram_chat_id and app.job_queue:
        app.job_queue.run_daily(nudge, time=time(hour=0, minute=30, tzinfo=KST))
        print("매일 00:30(KST) 넛지 활성화")

    print(f"봇 시작 — 백엔드 {API} 로 거래 저장. Ctrl+C 로 종료.")
    app.run_polling()


if __name__ == "__main__":
    main()

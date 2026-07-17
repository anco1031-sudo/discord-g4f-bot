#!/usr/bin/env python3
"""
Discord AI Bot — powered by g4f (GPT4Free) 🤖✨
Auto-select provider via model="default" → ไม่ต้องกลัว provider ดับ

Deploy: Render (worker type) → WebSocket heartbeat keep alive ตลอด
"""

import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands

import g4f

# ═══════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("discord-g4f")

# ═══════════════════════════════════════════════════════════
# Configuration (from environment variables)
# ═══════════════════════════════════════════════════════════
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
G4F_MODEL_STR = os.getenv("G4F_MODEL", "default")  # "default" = auto provider
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
COMMAND_NAME = os.getenv("COMMAND_NAME", "ask")
OWNER_ID = os.getenv("OWNER_ID")  # optional: restrict to specific Discord user ID

# Cooldown: กี่วินาทีให้ถามซ้ำได้ (ป้องกัน abuse)
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "30"))

# Timeout สำหรับ g4f แต่ละ request (ป้องกัน provider ค้าง)
G4F_TIMEOUT = int(os.getenv("G4F_TIMEOUT", "60"))


# ═══════════════════════════════════════════════════════════
# g4f Model Resolver
# ═══════════════════════════════════════════════════════════
def resolve_g4f_model(model_str: str):
    """Convert string "default" to g4f.models.default constant"""
    if model_str == "default" or not model_str:
        return g4f.models.default
    return model_str  # ถ้าส่งชื่อ model เฉพาะก็ส่ง string ตรง ๆ ได้


G4F_MODEL = resolve_g4f_model(G4F_MODEL_STR)

# ═══════════════════════════════════════════════════════════
# Discord Bot Setup
# ═══════════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True  # จำเป็นสำหรับอ่านข้อความคำสั่ง

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)

# ═══════════════════════════════════════════════════════════
# Events
# ═══════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    """เรียกเมื่อ bot พร้อมทำงาน"""
    logger.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"📡 WebSocket connected — Render worker = no sleep (heartbeat ตลอด)")
    logger.info(f"🤖 g4f model: {G4F_MODEL_STR} (auto provider)")
    logger.info(f"💬 Prefix: '{BOT_PREFIX}' | Command: '{COMMAND_NAME}'")
    logger.info(f"⏱️  Cooldown: {COOLDOWN_SECONDS}s | Timeout: {G4F_TIMEOUT}s")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{BOT_PREFIX}{COMMAND_NAME} <ถามอะไรก็ได้>",
        )
    )


@bot.event
async def on_command_error(ctx, error):
    """จัดการ error ของคำสั่ง — ตรงนี้จับเฉพาะที่หลุดจาก local handler"""
    if isinstance(error, commands.CommandNotFound):
        return  # ignore commands ที่ไม่มี

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(
            f"⚠️ ต้องใส่คำถามด้วยนะครับ\n"
            f"ใช้: `{BOT_PREFIX}{COMMAND_NAME} <คำถาม>`"
        )
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(
            f"⏳ รอ `{error.retry_after:.0f}` วินาทีก่อนถามอีกครั้งนะครับ"
        )
        return

    # error อื่น ๆ
    logger.error(f"Command error: {error}", exc_info=True)
    await ctx.reply(f"❌ เกิดข้อผิดพลาด: {str(error)[:500]}")


# ═══════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════

@bot.command(name=COMMAND_NAME)
@commands.cooldown(1, COOLDOWN_SECONDS, commands.BucketType.user)
async def ask(ctx, *, prompt: str):
    """🤖 ถาม AI อะไรก็ได้ — g4f auto-select provider"""
    if OWNER_ID and str(ctx.author.id) != OWNER_ID:
        await ctx.reply("⛔ เฉพาะ owner ที่กำหนดเท่านั้นถึงใช้ได้ครับ")
        return

    async with ctx.typing():
        try:
            logger.info(f"📩 [{ctx.author}] ask: {prompt[:80]}...")
            reply = await query_g4f(prompt)
            await send_long_message(ctx, reply)
            logger.info(f"✅ ตอบ {ctx.author} แล้ว ({len(reply)} chars)")

        except asyncio.TimeoutError:
            logger.warning(f"⏰ g4f timeout สำหรับ {ctx.author}")
            await ctx.reply("⏰ ขอโทษทีครับ g4f ไม่ตอบกลับภายในเวลาที่กำหนด — ลองถามใหม่นะครับ")

        except Exception as e:
            logger.error(f"❌ g4f error: {e}", exc_info=True)
            await ctx.reply(
                f"❌ ขอโทษทีครับ เจอปัญหา: {str(e)[:300]}\n"
                f"💡 ลองถามใหม่ภายหลัง หรือใช้คำถามอื่นดูนะครับ "
                f"(g4f auto provider จะลอง provider อื่นให้)"
            )


@bot.command(name="ping")
async def ping_cmd(ctx):
    """🏓 เช็คสถานะ bot + latency"""
    embed = discord.Embed(
        title="🏓 Pong!",
        color=discord.Color.green(),
    )
    embed.add_field(name="Latency", value=f"`{round(bot.latency * 1000)}ms`")
    embed.add_field(name="Status", value="✅ Online")
    embed.add_field(name="g4f Model", value=f"`{G4F_MODEL_STR}`")
    await ctx.reply(embed=embed)


@bot.command(name="status")
async def status_cmd(ctx):
    """📊 ดูสถานะ bot แบบละเอียด"""
    embed = discord.Embed(
        title="🤖 Bot Status",
        color=discord.Color.blue(),
    )
    embed.add_field(name="User", value=f"`{bot.user}`")
    embed.add_field(name="Latency", value=f"`{round(bot.latency * 1000)}ms`")
    embed.add_field(name="Guilds", value=f"`{len(bot.guilds)}`")
    embed.add_field(name="g4f Model", value=f"`{G4F_MODEL_STR}`")
    embed.add_field(name="Prefix", value=f"`{BOT_PREFIX}`")
    embed.add_field(name="Platform", value="`Render (Worker)`")
    await ctx.reply(embed=embed)


@bot.command(name="help")
async def help_cmd(ctx):
    """📖 แสดงวิธีใช้ bot"""
    embed = discord.Embed(
        title="🤖 Discord AI Bot Help",
        description=f"Bot AI ที่ใช้ **g4f auto-select provider** — ไม่ต้องกลัว provider ดับ!\n"
                    f"Provider ล่ม → ลองถามใหม่ g4f จะเลือก provider อื่นให้ auto",
        color=discord.Color.purple(),
    )
    embed.add_field(
        name=f"📝 `{BOT_PREFIX}{COMMAND_NAME} <ข้อความ>`",
        value="ถาม AI ด้วยข้อความอะไรก็ได้ (การบ้าน, ไอเดีย, เขียนโค้ด, ปรัชญา)",
        inline=False,
    )
    embed.add_field(
        name=f"🏓 `{BOT_PREFIX}ping`",
        value="เช็ค latency",
        inline=True,
    )
    embed.add_field(
        name=f"📊 `{BOT_PREFIX}status`",
        value="ดูสถานะ bot",
        inline=True,
    )
    embed.add_field(
        name=f"📖 `{BOT_PREFIX}help`",
        value="แสดง help นี้",
        inline=True,
    )
    embed.set_footer(text="🤖 g4f auto provider — ไม่ต้องใช้ API key!")
    await ctx.reply(embed=embed)


# ═══════════════════════════════════════════════════════════
# Core g4f AI Logic (native async — no ThreadPoolExecutor needed)
# ═══════════════════════════════════════════════════════════

async def query_g4f(prompt: str) -> str:
    """
    เรียก g4f ด้วย native async API (create_async)
    model=g4f.models.default → g4f เลือก provider ที่เวิร์คให้อัตโนมัติ

    มี timeout กัน provider ค้าง
    """
    try:
        # g4f มี create_async ให้ใช้ native async ได้เลย
        # ไม่ต้องใช้ ThreadPoolExecutor
        response = await asyncio.wait_for(
            g4f.ChatCompletion.create_async(
                model=G4F_MODEL,
                messages=[{"role": "user", "content": prompt}],
            ),
            timeout=G4F_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise  # ให้ caller จัดการ
    except Exception as e:
        raise RuntimeError(f"g4f ล้มเหลว: {e}") from e

    # g4f ตอบกลับเป็น string หรือ dict แล้วแต่ provider
    if isinstance(response, dict):
        content = (
            response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", str(response))
        )
    else:
        content = str(response)

    content = content.strip()
    if not content:
        raise RuntimeError(
            "g4f ส่งคืนข้อความว่าง — provider อาจล่มชั่วคราว "
            "ลองถามใหม่เดี๋ยว provider auto เปลี่ยนให้"
        )
    return content


async def send_long_message(ctx, text: str):
    """
    ส่งข้อความยาว ๆ โดยแบ่งให้ไม่เกิน Discord limit (2000 chars)
    มี delay เล็กน้อยระหว่าง chunk ป้องกัน rate limit
    """
    MAX_LEN = 2000

    if len(text) <= MAX_LEN:
        await ctx.reply(text)
        return

    # ตัดเป็น chunks
    chunks = [text[i:i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]

    # chunk แรก reply (mention)
    await ctx.reply(chunks[0])
    # ที่เหลือ send ตรง ๆ — หน่วง 1 วิ กัน Discord rate limit
    for chunk in chunks[1:]:
        await asyncio.sleep(1)
        await ctx.send(chunk)


# ═══════════════════════════════════════════════════════════
# แถม: auto-restart helper (ใช้ตอน development)
# ═══════════════════════════════════════════════════════════
# ถ้าอยากให้ bot auto-restart เมื่อ token ว่าง ไม่ต้องทำอะไร
# Render จะ restart ให้เองถ้า process crash

# ═══════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════

def main():
    if not DISCORD_TOKEN:
        logger.error("❌ กรุณา set environment variable: DISCORD_TOKEN")
        logger.error("   export DISCORD_TOKEN='your_token_here'")
        logger.error("   หรือใส่ใน Render Dashboard → Environment Variables")
        sys.exit(1)

    logger.info("🚀 กำลังเริ่ม Discord Bot...")
    logger.info(f"   g4f Model:  {G4F_MODEL_STR}")
    logger.info(f"   Prefix:     {BOT_PREFIX}")
    logger.info(f"   Command:    {COMMAND_NAME}")
    logger.info(f"   Cooldown:   {COOLDOWN_SECONDS}s")
    logger.info(f"   Timeout:    {G4F_TIMEOUT}s")
    logger.info(f"   Platform:   Render (Worker Type) → ไม่มี sleep!")
    logger.info("=" * 50)

    try:
        bot.run(DISCORD_TOKEN, log_handler=None)
    except discord.LoginFailure:
        logger.error("❌ Token ไม่ถูกต้อง! กรุณาตรวจสอบ DISCORD_TOKEN")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ ไม่สามารถรัน bot ได้: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

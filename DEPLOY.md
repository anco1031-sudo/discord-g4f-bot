# 🚀 Deploy Guide — Discord Bot + g4f บน Render (ฟรี!)

## 📦 Files ในโปรเจกต์

| File | คำอธิบาย |
|------|----------|
| `main.py` | ตัว bot — discord.py + g4f (model="default") |
| `requirements.txt` | dependencies |
| `render.yaml` | Render Blueprint (deploy อัตโนมัติ) |
| `.env.example` | ตัวอย่าง environment variables |

---

## 📋 ขั้นตอนที่ 1: สร้าง Discord Bot (ได้ Token)

1. ไปที่ https://discord.com/developers/applications
2. กด **New Application** → ตั้งชื่อ
3. ไปแท็บ **Bot** → กด **Reset Token** → **Copy Token** เก็บไว้
4. ใต้ **Privileged Gateway Intents** → เปิด **Message Content Intent** ✅
5. ไปแท็บ **OAuth2 > URL Generator**
   - Scopes: เลือก `bot` `applications.commands`
   - Bot Permissions: เลือก `Send Messages` `Read Messages` `Read Message History`
6. คัดลอก URL ที่ Generated → เปิดใน browser → เพิ่ม bot เข้า Server

✅ เสร็จ!

---

## 📋 ขั้นตอนที่ 2: Deploy ไป Render (Worker — ฟรี!)

### วิธี A: Deploy ด้วย Blueprint (render.yaml) — 🔥 แนะนำ

1. **Push โค้ดขึ้น GitHub**
   ```bash
   cd discord-g4f-bot
   git init
   git add .
   git commit -m "first commit"
   git remote add origin https://github.com/your-username/discord-g4f-bot.git
   git push -u origin main
   ```

2. **ที่ Render Dashboard**
   - ไป https://dashboard.render.com
   - กด **New +** → **Blueprint**
   - เชื่อม GitHub repo
   - Render จะอ่าน `render.yaml` อัตโนมัติ
   - ตอนสร้างจะถาม `DISCORD_TOKEN` → **ใส่ Discord Bot Token** ที่ได้จากขั้นตอนที่ 1
   - กด **Apply** → รอ deploy ~2-3 นาที

3. **เช็คว่าทำงาน**
   - ไปที่ Logs ใน Render → ควรเห็น `✅ Logged in as ...`
   - ไปที่ Discord → พิมพ์ `!ping` ใน channel ที่มี bot อยู่

### วิธี B: Deploy ด้วย Web Dashboard (Manual)

1. ที่ Render Dashboard → **New +** → **Worker**
2. เชื่อม GitHub repo
3. ตั้งค่า:
   - **Name**: `discord-g4f-bot`
   - **Region**: `Singapore` (ใกล้ไทยสุด)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: **Free** ✅
4. กด **Advanced** → **Add Environment Variable**:
   - `DISCORD_TOKEN` = `<token จากขั้นตอนที่ 1>`
   - `G4F_MODEL` = `default`
   - `BOT_PREFIX` = `!`
    - `COMMAND_NAME` = `ask`
    - `COOLDOWN_SECONDS` = `30`
    - `G4F_TIMEOUT` = `60`
5. กด **Create Worker** → รอ deploy

---

## ✅ วิธีเช็คว่า Bot ทำงานปกติ

### ที่ Render Dashboard
```
Logs → ควรเห็น:
  ✅ Logged in as MyBot#1234 (ID: 123456789)
  📡 WebSocket connected — Render จะไม่ sleep เพราะ heartbeat ตลอด
```

### ที่ Discord
```
!ping        → 🏓 Pong! Latency: `XXms`
!status      → แสดงสถานะ bot
!ask สวัสดี   → 🤖 AI ตอบกลับ
```

---

## ⚙️ Render Free Tier Limits (ต้องรู้!)

| Limit | ค่า |
|-------|-----|
| Instance hours | **750 ชม./เดือน** (~31 วัน — วิ่ง 24/7 พอดี) |
| RAM | **512 MB** |
| CPU | **0.1 vCPU** |
| Bandwidth | **100 GB/เดือน** |
| Sleep (worker) | **❌ ไม่มี sleep!** (WebSocket heartbeat keep alive) |
| Sleep (web service) | 15 นาที (แต่เราใช้ worker ไม่ใช่ web service) |

> 💡 **Worker type** ไม่มี HTTP sleep — bot จะรันตลอด 24/7
> ตราบใดที่ WebSocket เชื่อมต่อกับ Discord อยู่

---

## 🐛 Troubleshooting

| ปัญหา | สาเหตุ | วิธีแก้ |
|-------|--------|--------|
| `❌ Token ไม่ถูกต้อง` | DISCORD_TOKEN ผิด | เช็ค token ใน Discord Developer Portal |
| Bot ไม่ตอบสนอง | Token ไม่ถูก หรือ intent ไม่เปิด | เปิด **Message Content Intent** |
| g4f error | Provider ล่ม | model="default" จะเลือก provider อื่น auto |
| RAM ใกล้เต็ม | g4f กิน RAM | ลด max_workers หรือเปลี่ยน provider |
| Bot offline | ใช้ hours ครบ 750 | รอต้นเดือน หรืออัพเป็น Pro ($25) |

---

## 📈 Scale Up (เมื่อโตแล้ว)

```
g4f → ใช้ model="default" → auto provider ต่อไป
RAM → ถ้า 512MB ไม่พอ → อัพ Render Pro ($25/เดือน → 2GB RAM)
Scaling → เพิ่ม worker หรือย้ายไป VPS
```

---

## 🎯 คำสั่งที่ใช้งานได้

```
!ask <ข้อความ>     → ถาม AI อะไรก็ได้
!ping              → เช็ค latency
!status            → ดูสถานะ bot
!help              → แสดง help
```

สนุกกับการใช้งานนะครับ! 🚀

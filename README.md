# Discord AI Bot — 🤖✨

Discord bot powered by **g4f** (GPT4Free) with **auto provider failover**  
รันฟรีบน Render (worker type) — WebSocket heartbeat keep alive 24/7

## Features

- `!ask <question>` — ถาม AI อะไรก็ได้ (g4f auto-select provider)
- `!ping` — เช็ค latency
- `!status` — ดูสถานะ bot
- `!help` — แสดงคำสั่ง

## Deploy

1. สร้าง Discord Bot → https://discord.com/developers/applications
2. Fork repo → เชื่อมกับ Render (New+ → Blueprint)
3. ใส่ `DISCORD_TOKEN` → Apply

รายละเอียดเต็มใน [`DEPLOY.md`](DEPLOY.md)

## Tech Stack

- **discord.py** (WebSocket Gateway)
- **g4f** (model="default" → auto provider)
- **Render** (worker type, free tier)

# linkstash

Forward links from anywhere (X, Instagram, YouTube, email, browser) to a
Telegram bot; they get stored in Postgres, enriched by background workers, and
browsed via a small web UI behind Caddy.

## Architecture

- **bot** — Telegram long-poll bot (no inbound port). Locked to your user ID.
- **api** — FastAPI + Jinja UI on `127.0.0.1:8731`. Optional `POST /ingest`.
- **worker** — RQ worker; per-site processors (yt-dlp for YouTube, generic OG
  scraper for everything else).
- **db** — Postgres 16.
- **redis** — RQ broker.

All four Python services share one image; only the entrypoint differs.

## Setup

1. Create a bot via [@BotFather](https://t.me/BotFather), grab the token.
2. Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot).
3. `cp .env.example .env` and fill in `TELEGRAM_BOT_TOKEN`,
   `TELEGRAM_ALLOWED_USER_IDS`, and a real `POSTGRES_PASSWORD` (also update
   it inside `DATABASE_URL`).
4. `docker compose up -d --build`
5. In Telegram, open your bot and forward any message containing a URL.
   You should get back `Saved 1 link.`
6. Browse `http://127.0.0.1:8731/` from the host, or wire it through your
   existing Caddy with the snippet in `Caddyfile.snippet` (WG-restricted).

## Forwarding flows

- **X / Instagram / YouTube apps** — Share → Telegram → your bot (or a chat
  with the bot pinned). The forwarded message keeps the URL.
- **Browser (mobile or desktop)** — Share / "Open in Telegram" with the bot.
- **Email** — forward to a Telegram-connected address (e.g. via a Zapier/n8n
  bridge), or paste the URL into the bot manually. Native email→Telegram
  isn't built in yet.
- **Scripted** — set `INGEST_TOKENS=sometoken` in `.env`, then
  `curl -H "Authorization: Bearer sometoken" -d '{"url":"…"}' \
   -H "Content-Type: application/json" http://127.0.0.1:8731/ingest`

## Adding new processors

`app/processors/<name>.py` exporting `process(url) -> {"title","description","metadata"}`,
then register it in `PROCESSORS` in `app/processors/router.py`. New rows are
routed by `site` (set by `detect_site()` in `app/services.py`).

## Schema

Single `links` table — `url`, `source`, `site`, `status`, `title`,
`description`, `note`, `metadata_json`, `ingest_payload`, `error`,
`received_at`, `processed_at`. `Base.metadata.create_all` runs on every
service startup; no migrations yet.

# BTC Proxy Demo Bot

Bot trading lokal untuk proxy `BTC` memakai pair `cbBTC/USDC` dari `Meteora`.

## One-Liner Installer

Jalankan wizard installer lokal:

```bash
bash scripts/install_wizard.sh
```

Wizard ini akan:

- membuat `.env`
- menanyakan mode bot
- mengatur loop lokal
- mengatur ukuran paper trade
- menyiapkan akun demo internal bila kamu pilih mode `demo`

Strategi yang dipakai:

- `Supertrend` pada `5m` dan `30m`
- `Bollinger Bands`
- `RSI`
- `MACD`

Bot ini belum terhubung ke exchange untuk eksekusi order nyata. Fokus saat ini adalah:

- ambil candle publik
- hitung indikator
- evaluasi sinyal
- jalankan paper demo lokal
- simpan history posisi dan `PnL`

## Catatan Penting

- market default saat ini adalah `cbBTC/USDC`
- `cbBTC` dipakai sebagai proxy `BTC`, bukan `BTC` native exchange
- jadi bot ini cocok untuk `local strategy testing`, bukan live production trading

## Struktur Project

- `app/main.py`
  - entrypoint bot
- `app/config.py`
  - parser `.env`
- `app/data.py`
  - data provider `Meteora OHLCV`
- `app/indicators.py`
  - perhitungan indikator
- `app/strategy.py`
  - rule strategi entry dan exit
- `app/runtime.py`
  - loop bot
- `app/portfolio.py`
  - paper position, trade history, dan PnL history
- `STRATEGY.md`
  - spesifikasi strategi

## Kebutuhan

- `Python 3.14+`
- koneksi internet

Saat ini `requirements.txt` kosong karena implementasi memakai library bawaan Python.

## Setup

Cara paling cepat:

```bash
bash scripts/install_wizard.sh
```

Setelah itu jalankan:

```bash
python3 -m app.main
```

Cara manual:

1. Buat file `.env` dari `.env.example`
2. Sesuaikan konfigurasi
3. Jalankan:

```bash
python3 -m app.main
```

## Contoh `.env`

Contoh minimal untuk test lokal:

```env
BOT_MODE=dry_run
SYMBOL=cbBTC/USDC
STRATEGY_LABEL=cbBTC BTC proxy demo

DATA_SOURCE=meteora
METEORA_POOL_ADDRESS=7ubS3GccjhQY99AYNKXjNJqnXjaokEdfdV915xnCb96r
METEORA_POOL_NAME=cbBTC-USDC

SIGNAL_TIMEFRAME=5m
TREND_TIMEFRAME=30m
HISTORY_LIMIT=250

LOCAL_LIVE_LOOP=true
POLL_INTERVAL_SECONDS=30
MAX_LOOP_ITERATIONS=0

DATA_DIR=data
PAPER_TRADE_SIZE_USDC=1000
FEE_BPS=0

DEMO_ACCOUNT_COUNT=0
```

## Mode Bot

### `dry_run`

Mode ini cocok untuk test lokal paling aman.

- bot tetap ambil candle
- bot tetap hitung indikator
- bot tetap evaluasi sinyal
- bot tetap simpan state paper position dan PnL lokal
- bot tidak kirim order ke mana pun

### `demo`

Mode ini dipakai untuk simulasi multi akun internal dari `.env`.

- bot membaca `DEMO_ACCOUNT_COUNT`
- bot membaca akun `DEMO_1`, `DEMO_2`, dan seterusnya
- bot tetap belum terhubung ke exchange sungguhan

Contoh:

```env
BOT_MODE=demo
DEMO_ACCOUNT_COUNT=2

DEMO_1_NAME=demo_a
DEMO_1_API_KEY=dummy_key_1
DEMO_1_API_SECRET=dummy_secret_1

DEMO_2_NAME=demo_b
DEMO_2_API_KEY=dummy_key_2
DEMO_2_API_SECRET=dummy_secret_2
```

## Loop Lokal Live

Kontrol loop dilakukan dari `.env`:

- `LOCAL_LIVE_LOOP=false`
  - bot jalan sekali lalu selesai
- `LOCAL_LIVE_LOOP=true`
  - bot terus berjalan dalam loop
- `POLL_INTERVAL_SECONDS=30`
  - jeda antar evaluasi
- `MAX_LOOP_ITERATIONS=0`
  - `0` berarti tanpa batas
  - angka `> 0` cocok untuk test singkat

Contoh test cepat:

```env
LOCAL_LIVE_LOOP=true
POLL_INTERVAL_SECONDS=1
MAX_LOOP_ITERATIONS=3
```

## History PnL

Bot menyimpan paper trading history lokal selama berjalan.

Konfigurasi:

- `DATA_DIR=data`
- `PAPER_TRADE_SIZE_USDC=1000`
- `FEE_BPS=0`

File output:

- `data/portfolio_state.json`
  - state posisi aktif dan summary akun terakhir
- `data/trade_history.jsonl`
  - log entry dan exit
- `data/pnl_history.jsonl`
  - snapshot PnL tiap siklus

## Cara Test Sekarang

### Test 1: sekali jalan

Gunakan:

```env
BOT_MODE=dry_run
LOCAL_LIVE_LOOP=false
```

Lalu jalankan:

```bash
python3 -m app.main
```

### Test 2: loop singkat

Gunakan:

```env
BOT_MODE=dry_run
LOCAL_LIVE_LOOP=true
POLL_INTERVAL_SECONDS=1
MAX_LOOP_ITERATIONS=3
```

Lalu jalankan:

```bash
python3 -m app.main
```

### Test 3: demo multi akun internal

Gunakan:

```env
BOT_MODE=demo
LOCAL_LIVE_LOOP=true
POLL_INTERVAL_SECONDS=5
MAX_LOOP_ITERATIONS=3
DEMO_ACCOUNT_COUNT=2
```

Lalu isi akun demo di `.env` dan jalankan:

```bash
python3 -m app.main
```

## Output Yang Akan Terlihat

Saat bot jalan, kamu akan melihat:

- info mode bot
- jumlah candle yang berhasil diambil
- candle terakhir
- nilai indikator
- keputusan sinyal
- summary akun dan `PnL`

Jika ada trade valid, bot akan menulis log trade ke console dan ke file history.

## Default Source

Default source saat ini:

- source: `Meteora`
- pair: `cbBTC/USDC`
- pool: `7ubS3GccjhQY99AYNKXjNJqnXjaokEdfdV915xnCb96r`

Pool ini dipilih dari group `cbBTC-USDC` Meteora sebagai pool dengan `TVL` terbesar saat implementasi ini divalidasi.

## Status Saat Ini

Yang sudah tersedia:

- parser `.env`
- loop lokal live
- provider candle publik Meteora
- perhitungan indikator lokal
- evaluasi sinyal strategi
- paper position state
- history trade
- history `PnL`

Yang belum selesai:

- WebSocket live streaming
- integrasi exchange demo nyata
- order management sungguhan
- dashboard visual

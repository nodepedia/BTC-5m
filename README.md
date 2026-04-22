# BTC/USDT Auto Trade Bot

Fondasi bot trading lokal untuk proxy `BTC` menggunakan pair `cbBTC/USDC` dari Meteora dengan strategi:

- `Supertrend` pada `5m` dan `30m`
- `Bollinger Bands`
- `RSI`
- `MACD`

Bot mendukung dua mode eksekusi:

- `dry_run`
- `demo`

Pada mode `demo`, jumlah akun demo dibaca dari file `.env`.

Untuk local testing, bot mengambil data candle publik dari `Meteora OHLCV` dan memakai `cbBTC` sebagai proxy `BTC`, bukan `BTC/USDT` spot native exchange.

## Menjalankan

1. Salin `.env.example` menjadi `.env`
2. Isi konfigurasi yang dibutuhkan
3. Jalankan:

```bash
python3 -m app.main
```

## Loop Lokal Live

Kontrol loop lokal live dilakukan dari `.env`:

- `LOCAL_LIVE_LOOP=false`
  - bot jalan sekali lalu selesai
- `LOCAL_LIVE_LOOP=true`
  - bot terus polling candle dan evaluasi sinyal
- `POLL_INTERVAL_SECONDS=30`
  - jeda antar evaluasi
- `MAX_LOOP_ITERATIONS=0`
  - `0` berarti tanpa batas
  - angka `> 0` cocok untuk testing singkat

## History PnL

Bot sekarang menyimpan history paper PnL lokal selama berjalan.

Konfigurasi dari `.env`:

- `DATA_DIR=data`
- `PAPER_TRADE_SIZE_USDC=1000`
- `FEE_BPS=0`

File output:

- `data/portfolio_state.json`
  - state posisi dan summary akun saat ini
- `data/trade_history.jsonl`
  - riwayat entry dan exit
- `data/pnl_history.jsonl`
  - snapshot realized/unrealized PnL tiap siklus

## Default Source

Bot default memakai:

- data source: `Meteora`
- market: `cbBTC/USDC`
- default pool: `7ubS3GccjhQY99AYNKXjNJqnXjaokEdfdV915xnCb96r`

Pool default di atas dipilih dari group `cbBTC-USDC` Meteora sebagai pool dengan TVL terbesar saat validasi implementasi ini dibuat.

## Status Saat Ini

Yang sudah tersedia:

- struktur project
- parser konfigurasi `.env`
- parser multi akun demo
- provider candle publik Meteora
- perhitungan indikator lokal
- strategy engine berbasis candle real
- executor `dry_run`
- executor `demo` dalam bentuk scaffold aman

Yang belum selesai:

- streaming WebSocket / loop live berkelanjutan
- integrasi exchange demo
- order management nyata

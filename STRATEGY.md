# cbBTC/USDC Auto Trade Strategy

## Ringkasan

Strategi ini dipakai untuk local demo trading `cbBTC/USDC` sebagai proxy `BTC` dengan filter trend utama dari `Supertrend` pada dua timeframe:

- `5m`
- `30m`

Bot hanya boleh membuka posisi jika kedua timeframe menunjukkan arah trend yang sama. Jika arah trend berbeda, bot tidak melakukan entry.

Bot dirancang untuk mendukung mode percobaan dengan akun demo, bukan hanya `dry run`. Jumlah akun demo yang aktif harus bisa diatur dari file `.env`.

## Catatan Aset

Strategi lokal ini memakai `cbBTC` di Solana sebagai proxy untuk `BTC`.

- `cbBTC` adalah wrapped BTC dari Coinbase
- `cbBTC` backed `1:1` dengan BTC
- `cbBTC` bukan aset yang sama persis dengan `BTC` native exchange
- karena itu strategi ini harus dianggap sebagai `proxy BTC demo`, bukan `BTC/USDT` production bot

## Asumsi Implementasi Saat Ini

Supaya local demo bisa langsung berjalan, implementasi saat ini memakai asumsi berikut:

- `Supertrend 5m` dipakai sebagai filter trend cepat
- `Supertrend 30m` dipakai sebagai filter trend utama
- `Bollinger Bands`, `RSI`, dan `MACD` dievaluasi pada candle `5m`
- default `Supertrend` yang dipakai adalah `period 10` dan `multiplier 3`

Kalau nanti kamu ingin parameter `Supertrend` diubah, kita bisa pindahkan juga ke `.env`.

## Indikator

### 1. Supertrend

Dipakai untuk menentukan arah trend utama.

- Timeframe: `5m` dan `30m`
- Fungsi:
  - jika `5m` bullish dan `30m` bullish, hanya boleh cari `long`
  - jika `5m` bearish dan `30m` bearish, hanya boleh cari `short`
  - jika `5m` dan `30m` berlawanan, `tidak trading`

### 2. RSI

Dipakai sebagai salah satu konfirmasi entry dan exit.

- Level atas: `90`
- Level bawah: `10`

### 3. Bollinger Bands

Dipakai untuk area sentuh harga saat entry dan exit.

- Setting: default

### 4. MACD

Dipakai sebagai konfirmasi entry dan exit.

- Setting: default
- Yang dipakai adalah `perubahan warna pertama` pada histogram:
  - `first green`: histogram sebelumnya merah, lalu muncul bar hijau pertama
  - `first red`: histogram sebelumnya hijau, lalu muncul bar merah pertama

## Definisi Operasional

### Candle hit Bollinger Band

Yang dimaksud candle `hit` adalah harga candle menyentuh garis Bollinger Band melalui wick atau body. Tidak perlu menunggu candle close.

### Validasi Sinyal

Sinyal entry atau exit hanya sah jika:

- harga menyentuh Bollinger Band yang sesuai
- dan ada minimal satu konfirmasi tambahan:
  - `RSI` menyentuh level ekstrem yang sesuai, atau
  - `MACD` memberi perubahan warna pertama yang sesuai

Sinyal tidak valid jika hanya terjadi sentuhan Bollinger Band tanpa konfirmasi `RSI` atau `MACD`.

## Filter Trend

### Long mode

Aktif jika:

- `Supertrend 5m = bullish`
- `Supertrend 30m = bullish`

### Short mode

Aktif jika:

- `Supertrend 5m = bearish`
- `Supertrend 30m = bearish`

### No trade mode

Aktif jika:

- `Supertrend 5m` dan `Supertrend 30m` tidak searah

Dalam kondisi ini bot tidak boleh membuka posisi baru.

## Rule Entry dan Exit

### Entry Long

Posisi `long` boleh dibuka hanya jika filter trend bullish aktif, lalu terpenuhi:

1. candle menyentuh `lower Bollinger Band`
2. lalu ada salah satu konfirmasi berikut:
   - `RSI <= 10`
   - `MACD first green`

Rumus:

`Entry Long = Trend Bullish + Touch Lower BB + (RSI <= 10 OR MACD First Green)`

### Exit Long

Posisi `long` boleh ditutup jika terpenuhi:

1. candle menyentuh `upper Bollinger Band`
2. lalu ada salah satu konfirmasi berikut:
   - `RSI >= 90`
   - `MACD first red`

Rumus:

`Exit Long = Touch Upper BB + (RSI >= 90 OR MACD First Red)`

### Entry Short

Posisi `short` boleh dibuka hanya jika filter trend bearish aktif, lalu terpenuhi:

1. candle menyentuh `upper Bollinger Band`
2. lalu ada salah satu konfirmasi berikut:
   - `RSI >= 90`
   - `MACD first red`

Rumus:

`Entry Short = Trend Bearish + Touch Upper BB + (RSI >= 90 OR MACD First Red)`

### Exit Short

Posisi `short` boleh ditutup jika terpenuhi:

1. candle menyentuh `lower Bollinger Band`
2. lalu ada salah satu konfirmasi berikut:
   - `RSI <= 10`
   - `MACD first green`

Rumus:

`Exit Short = Touch Lower BB + (RSI <= 10 OR MACD First Green)`

## Ringkasan Logika Inti

- `Long` hanya saat dua `Supertrend` sama-sama bullish
- `Short` hanya saat dua `Supertrend` sama-sama bearish
- jika dua `Supertrend` tidak searah, bot tidak trading
- semua `entry` wajib: `Bollinger Band + (RSI atau MACD)`
- semua `exit` wajib: `Bollinger Band + (RSI atau MACD)`
- sentuh Bollinger Band saja tidak cukup

## Mode Eksekusi Bot

### 1. Dry Run

Mode ini hanya mengevaluasi sinyal tanpa mengirim order ke exchange.

Fungsi:

- validasi logika strategi
- melihat sinyal yang muncul
- mengecek alur bot tanpa transaksi

### 2. Demo Mode

Mode ini menjalankan strategi pada akun demo atau sandbox exchange. Berbeda dari `dry run`, mode ini tetap membuat order virtual ke akun demo agar perilaku bot bisa diuji lebih realistis.

Fungsi:

- menguji entry dan exit secara nyata di environment demo
- mengukur performa strategi
- menguji banyak akun demo sekaligus

### Prinsip yang Diinginkan

Bot harus mendukung jumlah akun demo yang bisa diatur lewat `.env`, sehingga satu instance bot dapat menjalankan strategi yang sama ke beberapa akun demo sekaligus.

## Kebutuhan Konfigurasi

Konfigurasi minimum yang perlu disiapkan:

- mode bot: `dry_run` atau `demo`
- jumlah akun demo aktif
- kredensial masing-masing akun demo
- symbol utama: `BTC/USDT`
- timeframe strategi

## Desain Demo Multi Account

### Perilaku Umum

- bot membaca mode dari `.env`
- jika mode adalah `dry_run`, bot tidak mengirim order
- jika mode adalah `demo`, bot membaca jumlah akun demo dari `.env`
- bot memuat daftar akun demo sesuai jumlah tersebut
- setiap akun demo menjalankan eksekusi order berdasarkan sinyal strategi yang sama

### Tujuan

Dengan desain ini:

- strategi hanya ditulis sekali
- eksekusi bisa diterapkan ke satu atau banyak akun demo
- pengujian lebih realistis dibanding `dry run`
- jumlah akun tidak perlu diubah dari kode, cukup dari `.env`

## Contoh Struktur `.env`

Berikut contoh format konfigurasi yang bisa dipakai saat implementasi:

```env
BOT_MODE=demo
SYMBOL=BTC/USDT
DEMO_ACCOUNT_COUNT=2

DEMO_1_NAME=demo_a
DEMO_1_API_KEY=your_demo_api_key_1
DEMO_1_API_SECRET=your_demo_api_secret_1

DEMO_2_NAME=demo_b
DEMO_2_API_KEY=your_demo_api_key_2
DEMO_2_API_SECRET=your_demo_api_secret_2
```

## Aturan Implementasi Konfigurasi

- jika `BOT_MODE=dry_run`, kredensial akun demo tidak wajib dipakai
- jika `BOT_MODE=demo`, bot wajib membaca `DEMO_ACCOUNT_COUNT`
- bot wajib memuat akun mulai dari index `1` sampai `DEMO_ACCOUNT_COUNT`
- jika ada akun yang tidak lengkap kredensialnya, bot harus menandai error akun tersebut dengan jelas
- bot tidak boleh silently skip konfigurasi yang rusak
- jika jumlah akun demo adalah `0`, maka mode `demo` dianggap tidak valid

## Versi Logika Singkat

### Long

- Cari trend bullish dari `Supertrend 5m` dan `30m`
- Entry di `lower BB` dengan konfirmasi `RSI 10` atau `MACD first green`
- Exit di `upper BB` dengan konfirmasi `RSI 90` atau `MACD first red`

### Short

- Cari trend bearish dari `Supertrend 5m` dan `30m`
- Entry di `upper BB` dengan konfirmasi `RSI 90` atau `MACD first red`
- Exit di `lower BB` dengan konfirmasi `RSI 10` atau `MACD first green`

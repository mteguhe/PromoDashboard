# Design Specification: Scraper Redesign — Multi-Source Adapter Pipeline
Tanggal: 2026-06-30
Status: Approved

---

## 1. Latar Belakang & Masalah

Scraper saat ini memiliki dua masalah utama:

1. **Noise tinggi** — artikel bukan promo masuk ke database karena validation gate terlalu longgar.
2. **Recall rendah** — sumber data terlalu sedikit (hanya 4 RSS feed), kategori baru (fashion, entertainment, event) tidak punya sumber sama sekali.

Root cause arsitektur: tabel DB terpisah per kategori (`flight_promos`, `food_promos`) menyebabkan bug routing saat kategori baru ditambahkan, dan tidak ada abstraksi sumber data yang bisa di-extend tanpa menyentuh `engine.py`.

---

## 2. Tujuan

- Mengganti dua tabel terpisah dengan satu tabel `promos` unified.
- Membangun sistem adapter per jenis sumber sehingga menambah sumber baru tidak memerlukan perubahan engine.
- Memperbaiki kualitas filtering: hanya data yang benar-benar promo yang masuk DB.
- Memprioritaskan portal terpercaya (Traveloka, Shopee, Tokopedia, dll), lalu sosmed, lalu RSS.

---

## 3. Database Schema

Ganti `flight_promos` dan `food_promos` dengan satu tabel:

```sql
CREATE TABLE promos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category        TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    brand_name      TEXT,
    promo_code      TEXT,
    discount_value  TEXT,
    min_transaction TEXT,
    expired_date    DATE,
    source_platform TEXT,
    source_url      TEXT UNIQUE,
    scraped_at      TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    created_at      TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_promos_category ON promos(category);
CREATE INDEX IF NOT EXISTS idx_promos_created_at ON promos(created_at);
```

Nilai valid untuk `category`: `flight`, `food`, `fashion`, `entertainment`, `event`.

Field spesifik per kategori (mis. `origin_city`/`destination_city` untuk flight, `locations` untuk food) dimasukkan ke `description` sebagai teks terstruktur. Tidak ada kolom tambahan per kategori.

### Migrasi

Script `db/migrate_to_unified.py`:
1. Buat tabel `promos` baru.
2. Copy semua baris dari `flight_promos` (dengan `category='flight'`) dan `food_promos` (dengan `category='food'`).
3. Rename tabel lama menjadi `flight_promos_backup` dan `food_promos_backup`.

---

## 4. Adapter Architecture

### 4.1 Kontrak Interface

Semua adapter mewarisi `BaseAdapter` dan mengimplementasikan satu method:

```python
# scraper/adapters/base.py
class BaseAdapter:
    def fetch(self) -> list[dict]:
        """Return list promo dicts dengan shape standar."""
        raise NotImplementedError
```

Shape standar setiap item:

```python
{
    "title": str,
    "description": str,
    "category": str,           # flight | food | fashion | entertainment | event
    "brand_name": str | None,
    "promo_code": str | None,
    "discount_value": str | None,
    "min_transaction": str | None,
    "expired_date": str | None,
    "source_platform": str,
    "source_url": str,
}
```

### 4.2 Adapter yang Dibangun (Prioritas B → C → A)

**Prioritas 1 — `PortalAdapter` (portal terpercaya, halaman promo publik)**

Target sumber (semua via HTTP GET + BeautifulSoup, tanpa headless browser):

| Portal | Kategori | Halaman Target |
|---|---|---|
| Traveloka | flight | Halaman promo penerbangan |
| Tiket.com | flight | Halaman deals |
| Shopee | food, fashion | Halaman voucher publik |
| Tokopedia | food, fashion | Halaman promo |
| Zalora | fashion | Halaman sale |
| Loket.com | event | Daftar event mendatang |
| GoFood / GrabFood | food | Halaman promo publik |

Setiap portal dikonfigurasikan di `scraper/config.py` dengan `url`, `category`, dan `css_selector` untuk elemen kartu promo.

> **Resiliensi**: Jika static HTTP GET + BeautifulSoup gagal mengekstrak konten dari suatu portal (misalnya karena JavaScript rendering), portal tersebut di-skip dengan log warning — bukan crash. Portal SPA seperti Shopee/Tokopedia dapat dikecualikan dari config jika terbukti tidak bisa di-scrape secara statis.

**Prioritas 2 — `SocialAdapter` (sosial media publik)**

| Platform | Pendekatan |
|---|---|
| Threads | Scrape halaman profil akun promo resmi (publik, tanpa login) |
| TikTok | oEmbed API untuk metadata + teks caption publik |
| Instagram | Scrape halaman publik akun brand via web (tanpa API) |

Social adapter hanya menarget akun resmi brand/promo yang sudah dikonfigurasikan, bukan search keyword umum (mengurangi noise).

**Prioritas 3 — `RssAdapter` (refactor dari `rss_scraper.py`)**

Refactor `scraper/rss_scraper.py` menjadi `scraper/adapters/rss_adapter.py`. Logic fetch dan extract tetap sama, tapi output disesuaikan ke shape standar. Tambah RSS source untuk kategori fashion dan entertainment di `config.py`.

### 4.3 Struktur File

```
scraper/
  adapters/
    __init__.py
    base.py
    portal_adapter.py
    social_adapter.py
    rss_adapter.py
  ai_parser.py          (dipertahankan, diperbaiki promptnya)
  parser.py             (dipertahankan sebagai regex fallback)
  config.py             (ditambah sumber baru)
  db_manager.py         (diupdate untuk tabel promos unified)
  engine.py             (diupdate, orchestrate semua adapter)
```

---

## 5. Validation Gate

Setelah AI/regex parser memproses setiap item, hasilnya melewati fungsi validasi sebelum insert ke DB:

```python
def validate_promo(parsed: dict) -> bool:
    has_signal = any([
        parsed.get("promo_code"),
        parsed.get("discount_value"),
        parsed.get("expired_date"),
    ])
    return bool(parsed.get("title")) and has_signal
```

Item yang tidak memiliki minimal satu dari `promo_code`, `discount_value`, atau `expired_date` setelah parsing langsung dibuang — tidak masuk DB. Ini adalah fix utama untuk masalah noise.

> **Catatan urutan**: Raw output adapter → AI/Regex Parser → `validate_promo()` → insert DB.

---

## 6. Perbaikan AI Parser

Tiga perubahan pada `scraper/ai_parser.py`:

1. **Gate `is_promo` lebih eksplisit** — instruksi sistem diperketat: "Jika artikel ini tidak mengandung informasi promo, diskon, atau voucher, kembalikan `is_promo: false` segera."
2. **Confidence score** — tambah field `confidence: float (0.0–1.0)` ke JSON schema Gemini. Jika `confidence < 0.7`, hasil diabaikan dan fallback ke regex parser.
3. **Category-aware prompt** — setiap parse call menyertakan konteks kategori sehingga Gemini tahu field apa yang relevan:
   - `flight`: fokus maskapai, rute, tanggal
   - `food`: fokus brand, minimal transaksi, lokasi
   - `fashion`: fokus brand, persentase diskon, periode sale
   - `entertainment`/`event`: fokus nama venue/event, tanggal, harga tiket

---

## 7. Engine Orchestration

`engine.py` diupdate dengan loop yang tidak lagi hardcode kategori:

```
run_all_adapters(db_path)
    ↓
for adapter in [PortalAdapter, SocialAdapter, RssAdapter]:
    raw_items = adapter.fetch()
    for item in raw_items:
        if source_url already in promos table → skip
        parsed = gemini_parse(item, category) or regex_parse(item, category)
        if validate_promo(parsed):
            db.insert_promo(parsed)   # satu method, satu tabel
```

Jadwal: Cron 08:00 & 15:00 WIB (tidak berubah dari implementasi saat ini).

---

## 8. Perubahan Frontend & API

- `app/api/promos/route.js` — ganti query dari `SELECT * FROM flight_promos WHERE ...` menjadi `SELECT * FROM promos WHERE category=? AND ...`
- `app/api/scrape/url/route.js` — tetap berfungsi, hanya update insert ke tabel `promos`
- `components/PromoCard.js` — tidak ada perubahan, sudah terima `category` sebagai prop

---

## 9. Urutan Implementasi

1. Migrasi schema DB (`migrate_to_unified.py` + update `schema.sql` + update `db_manager.py`)
2. Update API dan frontend ke tabel `promos`
3. Bangun `PortalAdapter` + tambah config portal
4. Bangun `SocialAdapter` + tambah config akun sosmed
5. Refactor `RssAdapter` + tambah RSS source baru
6. Perbaiki AI parser (prompt + confidence + category-aware)
7. Update `engine.py` untuk orchestrate semua adapter
8. Tulis/update tests untuk validation gate dan masing-masing adapter

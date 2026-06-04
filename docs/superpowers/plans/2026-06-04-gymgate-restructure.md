# GymGate — Tam Yeniden Yapılandırma & Eksik Özellikler Planı

**Hedef:** Dağınık phase1/phase2/phase3 yapısını tek temiz bir proje köküne taşı, teknik hataları düzelt, eksik özellikleri ekle, Phase 4'ü tamamla.

**Mimari:** `phase3/` kodu taban alınır (en güncel). Proje kökünde `app/` klasörü oluşturulur. phase1/phase2/phase3 klasörleri silinir. Docs, `docs/` altında tutulur.

**Teknoloji:** FastAPI, SQLAlchemy (async), PostgreSQL, Redis, Docker, GitHub Actions

---

## Hedef Dosya Yapısı

```
gymgate-backend/          ← proje kökü
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── redis_client.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py
│   │   └── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── gym.py
│   │   ├── admin.py
│   │   ├── member.py
│   │   ├── plan.py
│   │   ├── subscription.py
│   │   ├── credential.py
│   │   ├── gate_device.py
│   │   └── access_log.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── gym.py
│   │   ├── member.py
│   │   ├── plan.py
│   │   ├── subscription.py
│   │   ├── credential.py
│   │   ├── device.py
│   │   └── verify.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── gyms.py
│   │   ├── members.py
│   │   ├── plans.py
│   │   ├── subscriptions.py
│   │   ├── credentials.py
│   │   ├── devices.py
│   │   ├── verify.py
│   │   ├── access_logs.py
│   │   ├── occupancy.py
│   │   └── dashboard.py        ← YENİ
│   ├── services/
│   │   ├── __init__.py
│   │   └── verification.py
│   └── utils/
│       ├── __init__.py
│       ├── encryption.py
│       └── qr_generator.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_verify.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── DECISIONS.md
│   └── api-contract.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## TODO Listesi

### ADIM 1 — Dosya Yapısını Düzelt (Yeniden Yapılandırma)
- [ ] 1.1 Kök dizinde `app/` klasörünü oluştur, `phase3/app/` içeriğini kopyala
- [ ] 1.2 `requirements.txt` dosyasını `phase3/requirements.txt`'ten kök dizine kopyala
- [ ] 1.3 `.env` dosyasını `phase3/.env`'den kök dizine kopyala; `.env.example` oluştur
- [ ] 1.4 `docs/DECISIONS.md` ve `docs/api-contract.md` dosyalarını `phase1/`'den güncelle
- [ ] 1.5 `phase1/`, `phase2/`, `phase3/` klasörlerini sil
- [ ] 1.6 Kök `docs/` altındaki gereksiz/tekrar dosyaları temizle

### ADIM 2 — Kritik Hata: Lazy Load Düzelt
- [ ] 2.1 `app/services/verification.py` içinde `subscription.plan` lazy load hatasını düzelt
  - Sorun: `subscription.plan.name` — async SQLAlchemy lazy load desteklemez, çalışma zamanında `MissingGreenlet` hatası verir
  - Çözüm: Subscription sorgusu sırasında `selectinload(Subscription.plan)` ekle

### ADIM 3 — Performans: API Key Lookup Düzelt
- [ ] 3.1 `GateDevice` modeline `api_key_prefix` kolonu ekle (raw key'in ilk 8 karakteri)
- [ ] 3.2 `app/routers/devices.py`'de cihaz oluşturulurken prefix'i kaydet
- [ ] 3.3 `app/auth/dependencies.py`'de tüm cihazları çekmek yerine prefix ile filtrele
  - Sorun: Tüm cihazlar çekilip her biri için bcrypt çalışıyor (~200ms/cihaz) — 200ms hedefi risk altında
  - Çözüm: `WHERE api_key_prefix = key[:8]` ile filtrele, sadece eşleşenler için hash doğrula

### ADIM 4 — Eksik Özellik: Member Dashboard Endpoint
- [ ] 4.1 `app/routers/dashboard.py` oluştur
- [ ] 4.2 `GET /dashboard` endpoint'i ekle (JWT auth gerekli), şu verileri döndürsün:
  - Bugünün girişleri (access_logs'ta bugün GRANTED olanlar)
  - Toplam aktif üye sayısı
  - 7 gün içinde üyeliği bitecek üyeler
  - 30+ gün hiç gelmemiş üyeler
- [ ] 4.3 `app/main.py`'e dashboard router'ı ekle

### ADIM 5 — Eksik Özellik: Access Logs Filtreleme
- [ ] 5.1 `app/routers/access_logs.py`'de `GET /access-logs` endpoint'ine filtre parametreleri ekle:
  - `date_from`, `date_to` (tarih aralığı)
  - `member_id` (belirli üye)
  - `decision` (GRANTED, DENIED_EXPIRED vb.)
  - `limit` (default 100, max 500)

### ADIM 6 — Eksik Özellik: Members List Pagination & Arama
- [ ] 6.1 `app/routers/members.py`'de `GET /members` endpoint'ine ekle:
  - `page` (default 1), `per_page` (default 20, max 100)
  - `search` (first_name, last_name veya email'de arama)
  - `is_active` filtresi
  - `is_flagged` filtresi

### ADIM 7 — Phase 4: Dockerfile
- [ ] 7.1 Kök dizinde `Dockerfile` oluştur (Python 3.12-slim, uvicorn ile çalışır)

### ADIM 8 — Phase 4: Docker Compose
- [ ] 8.1 `docker-compose.yml` oluştur: `api` + `db` (postgres:16-alpine) + `redis` (redis:7-alpine)
- [ ] 8.2 Servisler arası bağımlılıkları (depends_on), volume'ları ve env dosyasını ayarla

### ADIM 9 — Phase 4: GitHub Actions CI
- [ ] 9.1 `.github/workflows/ci.yml` oluştur
- [ ] 9.2 Pipeline adımları: lint (ruff) → test (pytest) → her `main`'e push'ta çalışsın

### ADIM 10 — Phase 4: README
- [ ] 10.1 `README.md` oluştur:
  - Proje açıklaması
  - Kurulum talimatları (`docker-compose up`)
  - Endpoint listesi (özet)
  - Verification endpoint ortalama response süresi bölümü
  - `.env.example` açıklaması

---

## Düzeltilmeyecekler (Bilinçli Karar)

- `phase1/api-contract.md`'deki `"access": "granted"` formatı — implementasyon PDF'e göre doğru (`"decision": "GRANTED"`), contract belgesi tarihi; sadece docs güncellenecek
- `bcrypt<4.0.0` pin — passlib uyumluluğu için gerekli, değiştirilmeyecek

---

## Notlar

- Alembic migration'ları **bu plan kapsamında değil** — DB schema değişikliği olmadığı varsayılıyor (sadece `api_key_prefix` kolonu Adım 3'te ekleniyor, o ayrıca not edilecek)
- Deploy (Render.com) README'de belgelenecek ama otomatik CI deploy bu plana dahil değil (Render webhook'u manüel kurulum gerektirir)

# GymGate — İlerleme Takibi

> Bu dosya, projeye her dönüşte (özellikle `/clear` sonrası) okunmalı.
> Kurallar için bkz. `CLAUDE.md`.

## Genel Durum (2026-06-11 itibariyle)

### Tamamlananlar
- **Faz 1 (Tasarım)**: `docs/DECISIONS.md`, `docs/api-contract.md`, `docs/erd.dbml` mevcut.
- **Faz 2 (Build)**: FastAPI app yazılmış — modeller, router'lar (auth, gyms, members,
  plans, subscriptions, credentials, devices, verify, access_logs, occupancy, dashboard),
  QR üretimi, Fernet şifreleme, Redis occupancy counter.
- **Faz 3 (Secure)**: JWT (gym_admin) + API Key (gate_device) auth, rate limiting (60/dk),
  tenant isolation (`gym_id` filtreleri), Pydantic şemaları.
- **Faz 4 (Deploy) — kısmen**: Dockerfile + docker-compose (FastAPI+Postgres+Redis),
  GitHub Actions CI (lint + pytest).

### Eksikler / Yapılacaklar (öncelik sırası önerisi — henüz kesinleşmedi)
1. ~~Lokal ortamı kurup testleri çalıştırmak~~ — Tamamlandı (2026-06-11). `.venv` oluşturuldu,
   `requirements.txt` + pytest/pytest-asyncio/httpx kuruldu. `gymgate-postgres` ve
   `gymgate-redis` container'ları (host portları 5432/6379) ayağa kaldırıldı, `gymgate_test`
   DB oluşturuldu. `tests/conftest.py`'deki engine/session fixture'ı session-scope'tan
   function-scope'a çevrildi (event loop uyuşmazlığı sorununu çözdü). `test_verify.py`'deki
   yanlış 403 beklentisi 401 olarak düzeltildi (api-contract'a göre auth eksikliği = 401).
   Sonuç: 4/4 test geçiyor.
2. ~~Eski `phase1/`–`phase3/` klasörlerinin temizlenmesi~~ — Tamamlandı (2026-06-11),
   2 commit ile (`.gitignore` + pycache temizliği, phase1-3 klasörlerinin kaldırılması).
   phase4 zaten yoktu.
3. ~~`.gitignore` eklenmesi~~ — Tamamlandı (2026-06-11). `__pycache__/`, `*.pyc`, `.venv/`,
   `.env` ve hocadan gelen kişisel dosyalar (brief pdf, mail.txt, vs.) eklendi.
4. Eksik testlerin yazılması:
   - ~~verify'ın 6 karar dalı (GRANTED + 5 DENIED_*)~~ — Tamamlandı (2026-06-11),
     `tests/test_verify_decisions.py` + `tests/conftest.py`'ye `seed`/`make_member`
     fixture'ları eklendi. Ayrıca redis connection pool'un her testte (farklı event
     loop'larda) yeniden oluşturulması gerektiği bulundu (`reset_redis_pool` fixture).
   - ~~Rate limit testi, tenant isolation testleri~~ — Tamamlandı (2026-06-11),
     `tests/test_verify_security.py`. `make_member`/`seed` fixture'ları `make_gym`
     üzerine refactor edildi (birden fazla gym oluşturabilmek için).
   - Madde 4 tamamlandı. Toplam 12/12 test geçiyor.
5. Render'a deploy + gerçek `/verify` response time ölçümü + README güncellemesi.
   - Render deploy: **kullanıcı tercihiyle şimdilik atlandı** (hesap/repo durumu netleşince
     tekrar gündeme gelecek).
   - ~~`/verify` response time ölçümü + README~~ — Tamamlandı (2026-06-11). Lokal
     `docker-compose up` ile (Windows + Docker Desktop) ölçüldü: p50 ~215ms, p99 ~255ms,
     60 ardışık istek. README'deki "Performance" bölümü gerçek ölçümle güncellendi,
     Windows/Docker Desktop network overhead notu eklendi.
   - Not: `final-project-gym-system-api-1` imajı 6 gün önce build edilmiş, freeze/unfreeze
     sadeleştirmesinden (bu oturum öncesi) önceki kodu çalıştırıyor (`/subscriptions`
     yanıtında hâlâ `freeze_count`/`frozen_at` görünüyor). Gerekirse `docker compose
     up --build` ile yeniden build edilmeli.
6. Repo yapısının brief'teki "ayrı repo" şartına uygunluğunun teyidi
   (final proje ayrı repo olmalı, frontend de ayrı repo olmalı).

## Notlar / Kararlar
- **Mevcut kod CLAUDE.md kurallarına göre incelendi.** Genel yapı brief'e uygun ve
  öğrenci seviyesinde. Tek "fazla mühendislik" noktası subscription freeze
  limiti idi (`freeze_count`, `max_freezes`, `frozen_at` + dondurulan günü
  bitiş tarihine ekleme).
- **Karar**: Bu kısım basitleştirildi. Artık freeze/unfreeze sadece
  `active <-> frozen` durum geçişi yapıyor, limit veya tarih ötelemesi yok.
  Değişen dosyalar: `app/models/subscription.py`, `app/models/plan.py`,
  `app/schemas/plan.py`, `app/routers/subscriptions.py`, `docs/api-contract.md`.
- Diğer 3 nokta (services/verification.py ayrı dosya, API key hash+prefix,
  CI'da ruff lint) olduğu gibi bırakıldı — savunmada basitçe açıklanabilir
  (bkz. sohbet geçmişi).

## Sıradaki Oturumda Yapılacak İlk İş
- Render hesabı/repo durumu netleşince madde 5'in deploy kısmına dönülecek.
- Madde 6: Repo yapısının brief'teki "ayrı repo" şartına uygunluğunun teyidi.
- (İsteğe bağlı) `docker compose up --build` ile imajın güncel kodla yeniden build edilmesi.

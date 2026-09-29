# Demo Boya App — Boya Reçete Sistemi

Özel boya karışımı reçeteleri oluşturma, anlık maliyet/renk hesaplama ve şube bazlı
yetkilendirme içeren demo uygulama.

- **Backend:** FastAPI + async SQLAlchemy + PostgreSQL (`backend/`)
- **Frontend:** Framework'süz HTML/CSS/JS tek sayfa uygulaması (`frontend/`)

## Gereksinimler

- Python 3.11+ (proje 3.13 ile geliştirildi)
- PostgreSQL 14+ (veya aşağıdaki docker-compose)

## Kurulum

### 1. Veritabanı

Docker ile en kolayı:

```bash
docker compose up -d
```

Bu, `localhost:5432` üzerinde `paint_db` veritabanını (kullanıcı/şifre: `postgres`/`postgres`)
ayağa kaldırır. Kendi PostgreSQL kurulumunuzu kullanacaksanız `backend/.env` içindeki
`DATABASE_URL` değerini güncelleyin.

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python seed.py               # tabloları oluşturur + demo verileri ekler
uvicorn app.main:app --reload --port 8000
```

API dokümantasyonu: http://localhost:8000/docs

### 3. Frontend

`frontend/login.html` dosyasını tarayıcıda açın veya basit bir statik sunucuyla servis edin:

```bash
cd frontend
python -m http.server 5500
# http://localhost:5500/login.html
```

Backend farklı bir adresteyse, sayfada script'lerden önce `window.API_BASE_URL`
tanımlayın (varsayılan: `http://localhost:8000`).

## Demo Kullanıcılar

| Kullanıcı  | Şifre       | Rol     | Şube   |
|------------|-------------|---------|--------|
| admin      | admin123    | ADMIN   | Şube A |
| yetkili_a  | yetkili123  | YETKİLİ | Şube A |
| yetkili_b  | yetkili123  | YETKİLİ | Şube B |
| usta_a     | usta123     | USER    | Şube A |
| usta_b     | usta123     | USER    | Şube B |

Admin/Yetkili sol menüden aktif şubeyi değiştirebilir; veri erişimi backend'de
JWT'deki şube claim'i ile sınırlandırılır.

## Yapılandırma (`backend/.env`)

| Değişken                      | Varsayılan                       | Açıklama                                   |
|-------------------------------|----------------------------------|--------------------------------------------|
| `DATABASE_URL`                | `postgresql+asyncpg://...`       | Async SQLAlchemy bağlantı adresi           |
| `SECRET_KEY`                  | —                                | JWT imzalama anahtarı (prod'da değiştirin) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`                           | Token ömrü (dakika)                        |
| `CORS_ORIGINS`                | `*`                              | Virgülle ayrılmış origin listesi           |
| `SQL_ECHO`                    | `false`                          | SQL sorgularını logla                      |

## Migration'lar (Alembic)

Şema değişikliklerinde:

```bash
cd backend
alembic revision --autogenerate -m "aciklama"
alembic upgrade head
```

Uygulama açılışta eksik tabloları `create_all` ile de oluşturur (demo kolaylığı);
mevcut tablolarda kolon değişikliği için Alembic gereklidir.

## Testler

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

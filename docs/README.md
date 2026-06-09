# SaleOS — Master Context Document

> **For AI agents and future developers:** This file is your entry point. Read it first, then follow the document pointers below before touching any code. It captures every architectural decision, constraint, open question, and risk across all 13 source documents.

---

## Table of Contents

1. [What Is SaleOS?](#1-what-is-saleos)
2. [Document Map](#2-document-map)
3. [System Architecture at a Glance](#3-system-architecture-at-a-glance)
4. [Service Directory](#4-service-directory)
5. [Shared Infrastructure](#5-shared-infrastructure)
6. [Tech Stack (Mandatory)](#6-tech-stack-mandatory)
7. [Database Schema Overview](#7-database-schema-overview)
8. [Inter-Service Communication](#8-inter-service-communication)
9. [Auth & Security Model](#9-auth--security-model)
10. [AI Engine Strategy](#10-ai-engine-strategy)
11. [OCR Payment Verification Flow](#11-ocr-payment-verification-flow)
12. [Platform-Specific Constraints](#12-platform-specific-constraints)
13. [Docker Network Strategy](#13-docker-network-strategy)
14. [Environment Variables Reference](#14-environment-variables-reference)
15. [Architectural Issues & Risks Found in Documents](#15-architectural-issues--risks-found-in-documents)
16. [UX Concerns Identified](#16-ux-concerns-identified)
17. [Missing Specifications (Gaps)](#17-missing-specifications-gaps)
18. [Open Questions for the Owner](#18-open-questions-for-the-owner)
19. [Coding Standards](#19-coding-standards)
20. [Authorization Matrix](#20-authorization-matrix)

---

## 1. What Is SaleOS?

**SaleOS** (Omnichannel Sales Automation and E-commerce Core) is a multi-tenant SaaS platform built for Ethiopian merchants who sell primarily through social media. It unifies four social channels — Telegram, TikTok, Instagram, and Facebook — into a single automated system.

> **Phase 1 build order:** Telegram → TikTok → Instagram → Facebook. Each microservice is built fully (backend + frontend) before the next one starts.
> **YouTube:** Cancelled for Phase 1. Deferred to Phase 2. All YouTube-related code, SRS references, and risks are ignored until then.

**Core value propositions:**
- AI agents auto-reply to customers and guide them through checkout without human intervention
- A custom OCR API reads Ethiopian bank transfer screenshots (Telebirr, CBE Birr) and auto-verifies payments inside the chat
- Real-time inventory sync across all five channels prevents overselling
- Merchants can use one channel or the full suite; the system works either way
- A Central Web Hub with SSO dynamically shows only the modules the merchant has subscribed to

**Target market:** Ethiopian merchants (e-commerce vendors, brand owners, importers, retail operators) who use social media as their primary sales channel.

---

## 2. Document Map

Read in this order for full context:

### Proposal Documents (`docs/propousal/`)
| File | What It Covers |
|---|---|
| [SaleOs (Main).md](propousal/SaleOs%20(Main).md) | System overview, architecture topology, SSO, OCR flow, modular design |
| [SaleOs Telegram Microservice.md](propousal/SaleOs%20Telegram%20Microservice.md) | Telegram bot flows, Inline Keyboards, payment state machine |
| [SaleOs Tiktok Microservice.md](propousal/SaleOs%20Tiktok%20Microservice.md) | TikTok comment-to-DM, video publishing rules, viral traffic handling |
| [SaleOs Instagram Microservice.md](propousal/SaleOs%20Instagram%20Microservice.md) | Instagram webhook payload format, 24h window rules, API constraints |
| [SaleOs Facebook Microservice.md](propousal/SaleOs%20Facebook%20Microservice.md) | Facebook Feed-to-Messenger pipeline, Meta OAuth, async queuing |
| [SaleOs Youtube Microservice.md](propousal/SaleOs%20Youtube%20Microservice.md) | YouTube quota math, Shorts detection, resumable upload pipeline, n8n |

### SRS Documents (`docs/SRS/`)
| File | What It Covers |
|---|---|
| [SaleOs main SRS.md](SRS/SaleOs%20main%20SRS.md) | Full platform SRS: tech stack, folder structure, env vars, DB schema, API specs, auth flow, permissions matrix, UI requirements |
| [SaleOs main SRS Telegram.md](SRS/SaleOs%20main%20SRS%20Telegram.md) | Telegram SRS: aiogram config, dynamic bot manager, DB tables, API endpoints, UI layout, OCR fallback loop |
| [SaleOs main SRS Tiktok.md](SRS/SaleOs%20main%20SRS%20Tiktok.md) | TikTok SRS: OAuth lifecycle, encrypted token storage, comment webhook, rate-limiter, viral engagement loop |
| [SaleOs main SRS Facebook.md](SRS/SaleOs%20main%20SRS%20Facebook.md) | Facebook SRS: Meta OAuth, 60-day tokens, Messenger conversion loop, 24h window enforcement |
| [SaleOs main SRS Instagram.md](SRS/SaleOs%20main%20SRS%20Instagram.md) | Instagram SRS: Graph API, DM trigger keywords, Redis sliding window rate limiter, content studio |
| [SaleOs main SRS Instagram (1).md](SRS/SaleOs%20main%20SRS%20Instagram%20(1).md) | **YouTube SRS** (mislabeled file): Google OAuth, quota tracking, resumable upload pipeline, Shorts detection |
| [SaleOs main SRS Summery.md](SRS/SaleOs%20main%20SRS%20Summery.md) | Master Inventory & Database Core SRS: PostgreSQL schema, pessimistic locking, atomic decrement logic, Docker deployment |

> **Note:** `SaleOs main SRS Instagram (1).md` is the YouTube SRS — the filename is wrong. Rename it to `SaleOs main SRS Youtube.md` when the repo is set up.

---

## 3. System Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                     DOCKER NETWORK (saleos-net)              │
│                                                              │
│  ┌──────────────┐    ┌──────────────────────────────────┐   │
│  │   Nginx      │    │        Core Service (8000)        │   │
│  │  (Reverse    │───▶│  FastAPI | Auth | Products        │   │
│  │   Proxy)     │    │  Inventory | Orders | AI Engine   │   │
│  └──────────────┘    └──────────┬───────────────────────┘   │
│                                 │ X-Service-Token            │
│                    ┌────────────┼────────────┐               │
│                    ▼            ▼            ▼               │
│  ┌───────────┐  ┌──────┐  ┌────────┐  ┌──────────┐         │
│  │ Telegram  │  │TikTok│  │  Insta │  │ Facebook │         │
│  │   :8001   │  │ :8002│  │  :8003 │  │  :8004   │         │
│  └───────────┘  └──────┘  └────────┘  └──────────┘         │
│                                                              │
│  ┌───────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │ YouTube   │  │  PostgreSQL  │  │  Redis (shared)   │    │
│  │   :8005   │  │  (shared DB) │  │  Cache/Queue/FSM  │    │
│  └───────────┘  └──────────────┘  └───────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Architectural pattern:** Modular Monolith for data persistence (shared PostgreSQL) with microservice API isolation. Each service is independently deployable but shares the database and Redis.

---

## 4. Service Directory

| Service | Port | Role | Bot Library | Key External API | Phase |
|---|---|---|---|---|---|
| `saleos-core` | 8000 | Auth, inventory, orders, AI engine, central hub | — | Gemini / OpenAI, Ethiopian Bank OCR | 1 |
| `saleos-telegram` | 8001 | Telegram bot, checkout, broadcast | aiogram v3.x | Telegram Bot API | 1 — **Build first** |
| `saleos-tiktok` | 8002 | Comment replies, video publishing, DM (if API available) | httpx + Celery | TikTok Content Posting API | 1 |
| `saleos-instagram` | 8003 | DM automation, Reels publishing | httpx + Celery | Meta Graph API (Instagram for Business) | 1 |
| `saleos-facebook` | 8004 | Feed-to-Messenger, page management | httpx + Celery | Meta Graph API, Messenger Platform | 1 |
| `saleos-youtube` | 8005 | (YouTube service) | — | YouTube Data API v3 | **Phase 2 — NOT built in Phase 1** |

Each service has:
- Its own FastAPI backend
- Its own React/Vite/TypeScript frontend dashboard
- Its own `.env` configuration pointing to shared DB/Redis
- Standalone operation capability (works without the central hub)

---

## 5. Shared Infrastructure

| Component | Role | Notes |
|---|---|---|
| PostgreSQL | Single shared database | All services connect to `saleos_db`; tables are scoped by `merchant_id` |
| Redis | Cache + Session FSM + Celery broker + Rate limiter | Each service should use a different Redis database index (0–7) to avoid queue collisions |
| Celery | Async background task workers | One Celery worker per microservice; used for broadcasts, video uploads, rate-throttled DMs |
| Nginx | Reverse proxy + static file server | Routes traffic to the correct service by subdomain or path prefix |

---

## 6. Tech Stack (Mandatory)

These choices are non-negotiable — defined in the SRS documents.

### Frontend (every service)
- Vite + React (functional components only, zero class components)
- TypeScript (strict mode, no `any`)
- TailwindCSS (no inline styles)
- Shadcn UI (component library)
- React Query (TanStack Query) for data fetching
- Axios with JWT interceptors
- Zod for schema validation
- React Hook Form for form management

### Backend (every service)
- Python 3.12+
- FastAPI (all endpoints fully async)
- Pydantic v2 for validation
- SQLAlchemy 2.0 async engine
- Alembic for migrations
- httpx for outbound async HTTP calls

### Telegram-specific
- aiogram v3.x (the only async Python Telegram library that integrates cleanly with FastAPI)

### AI
- **Primary:** Gemini 1.5 Pro / Flash (Google AI Studio)
- **Fallback / Alternate:** OpenAI GPT-4o
- LangChain for LLM routing
- LangGraph for stateful multi-step checkout agent loops
- MCP (Model Context Protocol) support

### Infrastructure
- Docker + Docker Compose
- PostgreSQL
- Redis
- Celery
- Nginx

---

## 7. Database Schema Overview

All tables live in one PostgreSQL database. Every business-data table has a `merchant_id` foreign key for multi-tenant isolation.

### Core Tables (owned by `saleos-core`)
| Table | Purpose |
|---|---|
| `merchants` | Root business identities (UUID PK, business_name, contact_phone, contact_email) |
| `users` | All human operators: SUPER_ADMIN, ADMIN, MANAGER, STAFF, CUSTOMER — linked to `merchant_id` (nullable for Super Admins) |
| `products` | Master product catalog per merchant (SKU is unique per merchant) |
| `inventory_ledger` | Single source of truth for stock levels; `stock_level` + `reserved_stock` per product |
| `orders` | Global transaction log across all channels; `channel_source` enum: TELEGRAM, TIKTOK, FACEBOOK, INSTAGRAM, WEB_STORE |
| `order_items` | **Added (was missing from original SRS)** — line items linking an order to specific products. Columns: id (UUID PK), order_id (FK→orders), product_id (FK→products), quantity (INT), unit_price (NUMERIC 12,2), created_at. Without this table you can record a sale happened but not what was sold. |

### Core Tables — Added
| Table | Purpose |
|---|---|
| `merchant_payment_accounts` | **Added (was missing)** — Bank accounts merchants configure for manual payment. Columns: id (UUID PK), merchant_id (FK), bank_name (VARCHAR 100), account_number (VARCHAR 50), account_holder_name (VARCHAR 150), phone (VARCHAR 20, NULLABLE), is_active (BOOLEAN Default TRUE), created_at. Used by all microservices Phase 1 (no OCR). |

### Telegram Tables
| Table | Purpose |
|---|---|
| `telegram_bot_configs` | Per-merchant bot token (encrypted), welcome message, language_preference (AMHARIC/ENGLISH/AUTO), discussion_group_id, is_active |
| `telegram_customers` | Maps Telegram user_id + chat_id to merchant |
| `telegram_chat_sessions` | Conversational FSM state (Redis key: `telegram:fsm:{merchant_id}:{chat_id}`). DB row tracks last_interaction timestamp. |

### TikTok Tables
| Table | Purpose |
|---|---|
| `tiktok_bot_configs` | OAuth access_token, refresh_token (encrypted), token_expires_at |
| `tiktok_comments` | Comment log with status: PENDING, REPLIED, DM_SENT |

### Facebook Tables
| Table | Purpose |
|---|---|
| `facebook_bot_configs` | Encrypted 60-day Page Access Token, page_id, automation flags |
| `facebook_conversations` | Messenger thread tracking (PSID → merchant) |

### Instagram Tables
| Table | Purpose |
|---|---|
| `instagram_bot_configs` | Encrypted token, dm_trigger_keywords (JSONB), is_automated |
| `instagram_engagement` | Comment interaction log to prevent duplicate auto-replies |

### YouTube Tables
| Table | Purpose |
|---|---|
| `youtube_bot_configs` | Google OAuth tokens, channel_id, daily_quota_used (tracks 10k/day limit) |
| `youtube_videos` | Upload tracking: PENDING → UPLOADING → PUBLISHED / FAILED; is_short flag |

---

## 8. Inter-Service Communication

### Microservice → Core API
- Protocol: Internal HTTP REST
- URL pattern: `http://saleos-core:8000/api/v1/core/...`
- Security: Every request must include `X-Service-Token` header (a shared secret validated by the Core)
- Key endpoints microservices call on Core:
  - `POST /api/v1/core/inventory/reserve` — atomically decrement stock
  - `POST /api/v1/core/orders` — record a completed order
  - Core AI Engine calls for intent parsing (exact endpoint TBD)

### Atomic Inventory Decrement (Oversell Protection)
```
Microservice sends POST /api/v1/core/inventory/reserve
  → Core begins SQL transaction
  → SELECT stock_level FROM inventory_ledger WHERE product_id = '...' FOR UPDATE
  → If stock_level > 0: decrement stock_level, increment reserved_stock, COMMIT
  → If stock_level = 0: ROLLBACK, return 409 Conflict
```
This database-level pessimistic lock prevents two different channels from selling the last item simultaneously.

### Webhook Flows (External → Microservice)
| Service | External Webhook URL | Events |
|---|---|---|
| Telegram | `POST /api/v1/telegram/webhook/{merchant_id}` | All chat updates, button clicks, photo uploads |
| TikTok | `POST /api/v1/tiktok/webhook/{merchant_id}` | `comment.create` |
| Instagram | `POST /api/v1/instagram/webhook/{merchant_id}` | mentions, comments, messages |
| Facebook | `POST /api/v1/facebook/webhook/{merchant_id}` | `feed`, `messages` |

---

## 9. Auth & Security Model

- JWT (short-lived access token, HTTP-only cookie refresh token)
- Password hashing: Argon2 or bcrypt
- MFA (TOTP via authenticator app) required for SUPER_ADMIN and ADMIN roles
- JWT payload carries `merchant_id` + `role` claims — microservices read these to enforce authorization without a round-trip to Core
- JWT_SECRET is shared across all services (single secret in .env)
- Refresh tokens are blocklisted in Redis on logout
- OAuth tokens for third-party platforms (TikTok, Meta, Google) stored encrypted in PostgreSQL
- Internal API calls authenticated via `X-Service-Token` header

---

## 10. AI Engine Strategy

The Central AI Engine lives in `saleos-core`. Microservices call it rather than each embedding their own LLM logic.

**Flow:**
1. Microservice receives webhook event (comment, DM, etc.)
2. Microservice calls Core AI Engine with context (message text, merchant config, product inventory state)
3. Core AI parses intent, checks inventory, generates reply text
4. Core AI passes reply through a **Platform-Specific Adaptor** before returning:
   - Telegram adaptor: adds `<b>`, `<i>` HTML tags, appends inline keyboard buttons
   - TikTok adaptor: adds trending hashtags, enforces character limits
   - Instagram adaptor: adds hashtags, respects caption length
   - Facebook adaptor: strips markdown, maps emoticons
5. Microservice receives formatted reply and sends it via the platform API

**AI Models:**
- Primary: Gemini 1.5 Pro / Flash (Google AI Studio) — `GEMINI_API_KEY`
- Alternate/Fallback: OpenAI GPT-4o — `OPENAI_API_KEY`
- Prompts are localized for both Amharic and English (stored in `backend/app/prompts/`)

**LangGraph** is used for stateful multi-step flows (the checkout conversation where the agent tracks: product selection → cart confirmation → payment prompt → OCR verification → order confirmation).

---

## 11. OCR Payment Verification Flow

This is the most critical and unique feature. It appears in every channel microservice.

```
Customer selects product and clicks "Checkout via Telebirr/CBE Birr"
  → Bot sends: "Transfer [Amount] ETB to account XXXXXXXXXX and upload your screenshot"
  → Customer uploads screenshot image
  → Microservice downloads image into memory buffer (no disk write)
  → Microservice sends image to External Ethiopian Bank OCR API
      POST https://ocr.internal.platform/api/v1/verify-receipt
      Authorization: Bearer [OCR_TOKEN]

  SUCCESS PATH:
    OCR returns {"status": "success", "amount": 1200, "tx_id": "FT12345XYZ"}
    → Backend verifies amount matches cart total
    → Backend verifies tx_id is not a duplicate
    → POST /api/v1/core/inventory/reserve (atomic stock decrement)
    → POST /api/v1/core/orders (record order as PAID)
    → Bot replies: "Payment verified! Order #123 confirmed for delivery."

  FAILURE PATH (blurry, manipulated, duplicate, API timeout):
    → Order status set to PENDING_MANUAL_REVIEW in database
    → WebSocket push alert to merchant's dashboard UI
    → Bot replies: "Can't verify automatically. Your cart is saved. Contact support at [phone]."
    → Redis FSM state stays at AWAITING_PAYMENT_RECEIPT (user can retry)
```

---

## 12. Platform-Specific Constraints

Developers must know these hard limits before writing any automation logic:

### Telegram
- No native payment gateway for Ethiopian banks → OCR workaround is the solution
- Inline Keyboards are the primary UI element for product selection in chat
- Bot token is stored in DB (not .env) for dynamic multi-tenant management via aiogram

### TikTok
- Comment-to-DM requires TikTok Business Messaging API access (verify availability for Ethiopia)
- Rate limit: 200 DMs/hour per account — enforced via Redis distributed rate limiter
- Video publishing requires an actual video file — AI can only generate text/hashtags, not video
- Image carousels are supported as an alternative to video posts
- OAuth 2.0 required (not simple API tokens)

### Instagram
- 24-hour messaging window: after a user's last interaction, you have 24 hours to message them; after that you cannot send promo messages
- 200 automated DMs/hour/account — Redis sliding window limiter (alert at 180)
- 1 automated DM per unique user per 24 hours for comment triggers
- Webhook must respond 200 OK within 30 seconds or Meta retries 5 times
- Requires Meta App in Live mode with Advanced Access for `instagram_manage_messages`
- Aspect ratios: feed posts 4:5 to 1.91:1; Reels 9:16

### Facebook
- 24-hour messaging window (same as Instagram — Meta policy)
- 60-day Long-Lived Page Access Token (auto-refreshed by background job)
- Requires permissions: `pages_manage_engagement`, `pages_messaging`, `pages_read_user_content`
- Private Messenger thread opened via `comment_id` as recipient identifier (not user ID)
- Instagram and Facebook share the same Meta OAuth flow and webhook infrastructure

### YouTube
> **PHASE 2 ONLY — NOT built in Phase 1. Skip this entire section.**
> All YouTube constraints, risks, and SRS documents are deferred. Do not implement anything YouTube-related until Phase 2 begins.

---

## 13. Docker Network Strategy

All services communicate via a shared Docker external network named `saleos-net` (user has confirmed this network name exists on their Windows machine).

**Service hostnames inside Docker:**
```
saleos-core       → http://saleos-core:8000
saleos-telegram   → http://saleos-telegram:8001
saleos-tiktok     → http://saleos-tiktok:8002
saleos-instagram  → http://saleos-instagram:8003
saleos-facebook   → http://saleos-facebook:8004
postgres          → postgresql+asyncpg://user:pass@postgres:5432/saleos_db
redis             → redis://redis:6379
minio             → http://minio:9000  (S3-compatible self-hosted file storage)
```

Each microservice connects to the external network so it can communicate with `saleos-core` and shared infrastructure, but is also independently runnable by spinning up its own postgres + redis if needed for standalone testing.

---

## 14. Environment Variables Reference

The complete `.env` block is in [SaleOs main SRS.md](SRS/SaleOs%20main%20SRS.md) Section 4. Key vars:

```ini
# Core identity
APP_NAME=SaleOS
APP_ENV=production
SECRET_KEY=...
FRONTEND_URL=https://app.saleos.com
BACKEND_URL=https://api.saleos.com

# JWT
JWT_SECRET=...
JWT_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql+asyncpg://saleos_admin:pass@postgres:5432/saleos_db
REDIS_URL=redis://redis:6379/0

# AI
GEMINI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-proj-...

# Microservice URLs (used by core to call services)
TELEGRAM_SERVICE_URL=http://saleos-telegram:8001
TIKTOK_SERVICE_URL=http://saleos-tiktok:8002
INSTAGRAM_SERVICE_URL=http://saleos-instagram:8003
FACEBOOK_SERVICE_URL=http://saleos-facebook:8004

# OCR (built by external team — integrate when available; bypass in Phase 1 Telegram build)
EXTERNAL_ETHIOPIAN_BANK_OCR_API_URL=https://ocr.internal.platform/api/v1/verify-receipt
EXTERNAL_ETHIOPIAN_BANK_OCR_API_TOKEN=...

# Email
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=notifications@transactional.saleos.com
SMTP_PASSWORD=...

# ── ADDED (were missing from original SRS) ──────────────────────────────────

# Inter-service security token (Core validates this on every internal API call)
X_SERVICE_TOKEN=<generate: python -c "import secrets; print(secrets.token_hex(32))">

# Encryption key for OAuth tokens stored in DB (Fernet symmetric encryption)
ENCRYPTION_KEY=<generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Per-service Redis DB indexes (prevents Celery queue and cache key collisions)
REDIS_DB_CORE=0
REDIS_DB_TELEGRAM=1
REDIS_DB_TIKTOK=2
REDIS_DB_INSTAGRAM=3
REDIS_DB_FACEBOOK=4

# MinIO — self-hosted S3-compatible file storage (runs in Docker)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=saleos_minio_admin
MINIO_SECRET_KEY=<strong_secret>
MINIO_BUCKET_OCR=ocr-receipts
MINIO_BUCKET_MEDIA=merchant-media
MINIO_USE_SSL=false

# WebSocket (Core broadcasts real-time alerts to connected merchant dashboards)
WS_SECRET=<generate: python -c "import secrets; print(secrets.token_hex(16))">
```

---

## 15. Architectural Issues & Risks Found in Documents

These are real problems identified during the document review. Discuss with the owner before writing code.

### RISK-01: Shared Database Couples All Services
**Severity: Medium | Type: Architecture**
All 6 services share one PostgreSQL instance. A migration that alters a shared table (e.g., `orders`, `products`) affects every service simultaneously. A database crash takes down all services at once.
**Current mitigation:** Logical isolation via `merchant_id` scoping. This is an accepted trade-off for a startup.
**Recommendation:** Before any migration runs, all services must be stopped. Use Alembic migration locking or a migration coordinator.

### RISK-02: n8n vs. FastAPI in YouTube Documents
**Severity: N/A | Status: CANCELLED — YouTube is Phase 2**
Ignore until Phase 2.

### RISK-03: YouTube Quota Problem
**Severity: N/A | Status: CANCELLED — YouTube is Phase 2**
Ignore until Phase 2.

### RISK-04: TikTok Business Messaging API — DM Automation Unverified
**Severity: HIGH | Type: External Dependency**
TikTok's Business Messaging API (required for private DM automation) has restricted global availability. There is NO technical bypass for this — a VPS in a different region does not help because the restriction is at the API developer program level, not at the network/IP level. TikTok decides which businesses get DM API access regardless of where the server is hosted.

**Options (decided by owner):**
1. **Apply for TikTok Developer Partner Program** — merchants must apply individually; approval takes weeks/months
2. **Phase 1 TikTok = Comment-reply-only** — the bot publicly replies to comments (this IS available to all business accounts). In the reply it tells users: "DM us directly to order." No automated DM is sent. This is the safest approach.
3. **Phase 2 TikTok DMs** — once a merchant's account gets approved for Business Messaging API, the DM flow switches on automatically

**Recommended decision:** Build TikTok Phase 1 as comment-reply-only + video publishing. Add DM automation as a feature flag that activates per-merchant when API access is confirmed.

### RISK-05: WebSocket Infrastructure
**Severity: RESOLVED | Type: Decision Made**
**Decision:** FastAPI native WebSockets in `saleos-core`.
- Core exposes: `GET /ws/alerts/{merchant_id}` (WebSocket upgrade, JWT auth required)
- When any microservice creates a PENDING_MANUAL_REVIEW event, it calls: `POST /api/v1/core/internal/alert` with `X-Service-Token`
- Core pushes the alert payload to the merchant's connected WebSocket client
- Frontend connects once at login and keeps the connection open
- If the connection drops, frontend reconnects with exponential backoff
- This is centralized (one WebSocket server) and avoids duplicating real-time logic across 4 services

### RISK-06: Redis Database Index Collisions
**Severity: RESOLVED | Type: Configuration**
**Decision:** Each service uses a dedicated Redis DB index. Defined in env vars (Section 14):
- db/0: Core cache + session
- db/1: Telegram FSM + Celery
- db/2: TikTok Celery + Rate limiter
- db/3: Instagram Celery + Rate limiter
- db/4: Facebook Celery

### RISK-07: orders Table Missing order_items
**Severity: RESOLVED | Type: Schema**
**Fix applied:** `order_items` table added to schema (see Section 7). Table: `(id UUID PK, order_id FK→orders, product_id FK→products, quantity INT NOT NULL, unit_price NUMERIC(12,2) NOT NULL, created_at TIMESTAMP)`.

### RISK-08: X-Service-Token Missing from Env Vars
**Severity: RESOLVED | Type: Configuration**
**Fix applied:** `X_SERVICE_TOKEN` added to env vars block (Section 14).

### RISK-09: Two Different Schemas for orders.customer_info
**Severity: RESOLVED | Type: Inconsistency**
**Decision:** Use both fields together on the `orders` table:
- `customer_id` (UUID, FK→users, NULLABLE) — for registered SaleOS users
- `customer_info` (JSONB, NULLABLE) — for anonymous social media buyers (Telegram user, TikTok commenter, etc.) who are not in the `users` table
A social media order will have `customer_id = NULL` and `customer_info = {"name": "...", "telegram_id": 123456, "phone": "..."}`.

### RISK-10: No API Gateway Specified
**Severity: RESOLVED | Type: Architecture**
**Decision:** Nginx is the API gateway for all services. Path-based routing in `nginx.conf`:
- `/api/v1/auth/`, `/api/v1/core/`, `/ws/` → `saleos-core:8000`
- `/api/v1/telegram/` → `saleos-telegram:8001`
- `/api/v1/tiktok/` → `saleos-tiktok:8002`
- `/api/v1/instagram/` → `saleos-instagram:8003`
- `/api/v1/facebook/` → `saleos-facebook:8004`

All CORS is configured once in Nginx. Services run behind the gateway and don't need their own CORS headers for external requests.

---

## 16. UX Concerns Identified

### UX-01: YouTube — PHASE 2, SKIP
Deferred with the rest of YouTube.

### UX-02: Cross-Channel PENDING_MANUAL_REVIEW Consolidation
When OCR fails on Telegram and again on Instagram, those alerts appear on separate dashboards. A merchant should have one unified "Manual Review Inbox" in the Central Hub showing all pending OCR reviews across all channels, not five separate pages.

### UX-03: Onboarding Flow Absent from All Documents
There is no documented merchant onboarding flow. A new merchant needs to: register → verify email → enable MFA → subscribe to channels → connect each platform (OAuth for TikTok/Meta/Google, bot token for Telegram) → add products → go live. This multi-step wizard is not designed in any SRS.

### UX-04: Facebook 24-Hour Window Expiry — Silent Failure Risk
If a Messenger conversation stalls for 24 hours and the merchant's staff tries to send a message manually via the dashboard, the API will silently reject it (or return a 400). The UI must show a clear "Window Closed — Re-engage Required" status on stale conversations.

### UX-05: TikTok Video-Only Gate Warning
When a merchant tries to auto-post to TikTok and has no video file, the system blocks them. The UX for this error state ("TikTok requires a video asset — AI can generate text/hashtags but you must upload a video") is defined but should also be surfaced proactively before the merchant even starts typing their prompt.

---

## 17. Missing Specifications (Gaps)

Items that need to be designed before the relevant service can be coded:

| Gap | Affects | Status | Notes |
|---|---|---|---|
| `docker-compose.yml` | All services | **Open** | Will be written when first service (Telegram) is complete |
| Media / file storage | All services | **RESOLVED** | MinIO self-hosted Docker container. Buckets: `ocr-receipts`, `merchant-media`. Env vars defined in Section 14. |
| WebSocket implementation | All services | **RESOLVED** | Core-centralized FastAPI WebSocket. See RISK-05. |
| Encryption key management | TikTok, Meta, Google | **RESOLVED** | Use Python `cryptography.fernet.Fernet`. Key in `ENCRYPTION_KEY` env var. |
| `order_items` table | Core | **RESOLVED** | Added to schema. See RISK-07 and Section 7. |
| Merchant onboarding wizard | Central Hub UI | **Open** | Design before Central Hub UI build |
| Centralized logging | All services | **Open** | Use Python `structlog` for now; output to stdout so Docker captures it. Full stack (Loki/Grafana) in Phase 2. |
| Health check endpoints | All services | **Open** | Add `GET /health` to every FastAPI service before Docker Compose is written |
| CI/CD pipeline | All services | **Open** | Deferred |
| YouTube items | YouTube | **N/A** | Phase 2 |
| TikTok DM availability | TikTok | **RESOLVED** | No bypass possible. Build as comment-reply-only Phase 1. See RISK-04. |
| `X_SERVICE_TOKEN` env var | Core + all services | **RESOLVED** | Added to Section 14. |
| `ENCRYPTION_KEY` env var | TikTok, Meta, Google | **RESOLVED** | Added to Section 14. |
| Per-service Redis DB indexes | All services | **RESOLVED** | Added to Section 14. See RISK-06. |
| OCR API integration | All services | **DEFERRED** | OCR built by external team. Integrate when they provide access. Telegram Phase 1 uses manual payment fallback (bank account + merchant contact). |

---

## 18. Open Questions for the Owner

Previously answered decisions are removed. Remaining open items:

1. **Telegram — channel type:** Does the merchant operate a Telegram **Channel with a linked Discussion Group** (comments under posts appear in the group), or just a **Group/Supergroup** directly? Or both? This changes the bot admin permissions and event listener setup significantly. *(This is the most critical question before Telegram build begins — see Section 21.)*

2. **Language support:** Should the AI respond in Amharic, English, or auto-detect and respond in the same language the customer wrote in?

3. **TikTok DM:** Confirmed as comment-reply-only for Phase 1. When TikTok builds are started, confirm if any merchant has gotten Business Messaging API access.

4. **Merchant onboarding wizard:** Design needed before Central Hub UI. What steps do you want in the onboarding flow?

3. **TikTok DM API availability?** Have you verified TikTok Business Messaging API access from Ethiopia? If not available, TikTok becomes publish-only (no DM automation).

4. **orders.customer_info schema?** Use FK + JSONB together (see RISK-09), or just JSONB for all social buyers?

5. **WebSocket approach?** Should Core broadcast OCR alerts via WebSocket, or should each microservice maintain its own WebSocket server?

6. **Centralized logging?** Do you want structured logging (structlog → file), or a full stack (Grafana + Loki, or ELK)?

7. **Per-merchant Google Cloud Project for YouTube?** Confirmed that each merchant must set up their own? Or do you plan a pooled quota approach via third-party posting APIs (Blotato/PostPeer)?

8. **OCR API status?** Is the external Ethiopian Bank OCR API already built and available, or is it also part of this project's build scope?

9. **File naming:** Should `SaleOs main SRS Instagram (1).md` be renamed to `SaleOs main SRS Youtube.md`?

---

## 19. Coding Standards

Enforced across all services. Never deviate.

### Backend (Python)
- All endpoints and DB calls must be `async/await` — no blocking I/O
- Every function parameter and return type must have explicit type annotations
- Three-layer separation: `api/` (routing) → `services/` (business logic) → `repositories/` (SQL only)
- One class = one responsibility (SOLID)
- No hardcoded credentials anywhere in code

### Frontend (React/TypeScript)
- Functional components only — zero class components
- No `any` type — define explicit interfaces for every API response
- All styling via Tailwind utilities — no inline `style=` props
- Repeated layouts extracted to `src/components/`

### Folder structure per service
```
service-root/
├── frontend/
│   └── src/
│       ├── assets/, components/, constants/, hooks/
│       ├── layouts/, pages/, routes/, services/
│       ├── store/, styles/, types/, utils/
│       └── App.tsx, main.tsx
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic v2 schemas
│   │   ├── services/     # Business logic
│   │   ├── repositories/ # Database CRUD
│   │   ├── middleware/   # Auth, CORS, rate limiting
│   │   ├── core/         # JWT, settings, security
│   │   ├── agents/       # LangGraph agents (core service only)
│   │   ├── prompts/      # Amharic + English LLM prompts (core only)
│   │   ├── tasks/        # Celery background jobs
│   │   └── utils/        # Helpers
│   ├── tests/
│   └── migrations/       # Alembic
├── docker/
│   ├── frontend.Dockerfile
│   ├── backend.Dockerfile
│   └── nginx.conf
└── .env.example
```

---

## 20. Authorization Matrix

| Capability | Super Admin | Admin (Owner) | Manager | Staff | Customer |
|---|---|---|---|---|---|
| Modify global billing / subscription tiers | YES | NO | NO | NO | NO |
| Provision / revoke merchant microservices | YES | NO | NO | NO | NO |
| Configure merchant system settings | NO | YES | NO | NO | NO |
| Invite users, manage roles | NO | YES | YES | NO | NO |
| Modify products and inventory | NO | YES | YES | YES | NO |
| Force manual override on OCR pending | NO | YES | YES | NO | NO |
| View order logs and analytics | NO | YES | YES | YES | NO |
| Initiate manual cross-platform post | NO | YES | YES | YES | NO |
| View own storefront purchases / profile | NO | NO | NO | NO | YES |

MFA (TOTP) is required for SUPER_ADMIN and ADMIN at login.

---

---

## 21. Telegram Microservice — Phase 1 Scope (Build First)

This is the exact agreed scope for the first working build. Nothing outside this list is built in Phase 1.

### Confirmed architecture (decided 2026-06-07)

**Telegram setup type:** Channel + Linked Discussion Group (Option A)
- Merchant has a public Telegram Channel where they post products
- Channel has a linked Discussion Group where customers can comment
- Bot must be admin of the Discussion Group to read and reply
- When customer comments on a channel post, Telegram delivers it as a Discussion Group message

**Three-part Telegram microservice:**

| Part | Who Uses It | Tech | Notes |
|---|---|---|---|
| Admin Panel | Merchant (desktop) | Vite + React + TS | Bot config, bank accounts, products, live chats, order fallbacks, setup guide |
| Mini App | Customer (inside Telegram) | Vite + React + TS, mobile-first | Product catalog, cart, full order + bank info, Telegram Web App API |
| Bot Backend | Everyone via bot | FastAPI + aiogram v3 | Webhook handler, Discussion Group listener, DM AI agent, LangGraph FSM |

### What the Telegram bot does in Phase 1

| Feature | Details |
|---|---|
| **AI reads public comments** | Bot is admin of Discussion Group. When customer comments under a channel post, AI reads it and replies publicly with product info or general answer. |
| **Public reply + buttons** | Public reply includes two InlineKeyboard buttons: `[Open Store 🛍️]` → opens Mini App. `[Chat with Bot 💬]` → deep link (`t.me/{bot}?start=...`) that opens private DM. |
| **Private DM AI agent** | In DM, AI answers questions about products, recommends items with images and details. Customer can ask about multiple products, AI builds context. |
| **Multi-product cart in DM** | Customer says "I want 2 Nike shoes and 1 jacket". Bot tracks this in Redis FSM. Shows itemized cart with total price. |
| **Phase 1 payment output** | No OCR. Bot sends: bank account name, account number, holder name (from merchant's admin config) + total amount + merchant phone/contact. |
| **Post to Channel** | Merchant writes caption + uploads image in admin panel → backend posts it to the Channel via bot. |
| **Mini App — full order flow** | Customer browses products, adds to cart, sees bank payment info, submits order — all inside the Mini App without touching DM. |

### Key technical decisions made

| Decision | Choice | Reason |
|---|---|---|
| Products in Telegram admin panel | YES — merchants can add/edit products from Telegram admin panel (calls Core products API) | Convenience for merchants who only use Telegram |
| Mini App capability | Full order flow inside Mini App (browse + cart + checkout) | Better UX — no need to switch to DM for payment |
| Bot language | Merchant configures (Amharic / English / Auto-detect) in admin settings | Flexibility per merchant preference |
| Mini App URL | One URL, reads `merchant_id` from Telegram's secure `initData` | Simple maintenance, one deployment |

### Critical Telegram technical constraint (important for developers)

**Bots cannot initiate private DMs with users who haven't started the bot first.**
Workaround: The bot's public reply in the Discussion Group includes a deep link button:
```
[Chat with Bot 💬] → https://t.me/{bot_username}?start=product_{product_id}
```
When the customer clicks this, Telegram opens the bot's DM and automatically sends `/start product_{product_id}` — this counts as the user initiating the conversation, so the bot can now reply.
The bot extracts the `product_id` from the start payload and greets the customer with the specific product they commented on.

### What is NOT in Phase 1 Telegram

- OCR payment verification — waiting for external team; integrate when they provide API access
- Full LangGraph checkout FSM with payment state machine — deferred until OCR is available
- Celery broadcast (mass message to all users) — after basic bot is stable
- Analytics dashboard

### Telegram bot token management

- Merchant creates their own bot via Telegram BotFather and copies the token
- Token is entered in the SaleOS admin panel (never in any .env file)
- Backend stores token encrypted in `telegram_bot_configs` and dynamically registers the webhook via aiogram's `setWebhook`
- Changing token via UI takes effect immediately (old webhook deleted, new one registered)

### Discussion Group setup — merchant onboarding step

After entering their bot token, the admin panel shows a setup guide:
1. "Go to your Channel → Settings → Discussion → Link a group"
2. "Add your bot (@{bot_username}) as an admin of the linked Discussion Group"
3. "Come back here and click Verify" → backend calls `getChat` on the Discussion Group to confirm bot has admin rights
4. If verified: green checkmark, bot is live. If not: specific error message explaining which permission is missing.

---

*Last updated by Claude Code — 2026-06-07. Incorporates owner decisions: YouTube Phase 2, MinIO storage, WebSocket centralized in Core, order_items table added, TikTok DM comment-reply-only Phase 1, OCR deferred. Update this file whenever architectural decisions change.*

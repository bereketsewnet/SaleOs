# **Software Requirements Specification (SRS)**

## **For SaleOS (Centralized Omnichannel Operating System)**

## **1\. Project Overview**

### **1.1 Project Name**

* **Name:** SaleOS (The operating system combining Omnichannel Sales Automation and E-commerce Core).

### **1.2 Project Type**

* **Primary Classifications:** SaaS, CRM, AI Agent Suite, E-commerce Core Platform.

### **1.3 Business Goal**

To unify fragmented social commerce channels (Telegram, TikTok, Facebook, Instagram, YouTube) and localized transaction processing into a singular, cohesive enterprise-grade e-commerce operating system. SaleOS acts as the ultimate centralized orchestration hub, enabling merchants to handle decentralized customer interactions, automate context-aware marketing creation, manage multi-channel stock levels atomically, and automate payment clearing natively inside Ethiopia and the broader African digital commerce landscape.

### **1.4 Target Users**

* **SaaS Super Admins:** Operators managing platform global health, subscription tiers, merchant billing, and API system routes.  
* **Merchants / Business Admins:** E-commerce vendors, brand owners, importers, and retail store operators in Ethiopia using social media as their primary sales channels.  
* **Merchant Staff / Managers:** Sales representatives, delivery coordinators, and inventory clerks managing localized customer tickets and stock levels.  
* **End Customers:** Consumers interacting via social media messaging apps, public comment threads, or the centralized SaleOS web storefront.

### **1.5 Expected Outcome**

A bulletproof, production-ready, highly parallel web ecosystem that eliminates manual overhead for merchants. The system automatically turns social interactions into verified sales items, tracks item depletion down to the millisecond across separate channels, hooks smoothly into custom external vision services (Ethiopian Bank OCR), and hosts an independent web e-commerce channel dynamically linked to social touchpoints.

## **2\. Mandatory Tech Stack**

### **2.1 Frontend Architecture**

* **Build Tool:** Vite  
* **Core Library:** React (Functional Components Only)  
* **Language:** TypeScript (Strict Mode Enforced)  
* **Routing:** React Router  
* **Data Fetching & State Synchronization:** React Query (TanStack Query)  
* **HTTP Client:** Axios  
* **Styling Engine:** TailwindCSS  
* **Component Library:** Shadcn UI  
* **Schema Validation:** Zod  
* **Form Management:** React Hook Form

### **2.2 Backend Architecture**

* **Language Run-time:** Python 3.12+  
* **Framework:** FastAPI (Fully Asynchronous Endpoints)  
* **API Documentation:** Swagger / OpenAPI (Native auto-generation)  
* **Data Parsing & Validation:** Pydantic v2  
* **ORM:** SQLAlchemy 2.0 (Async Engine execution)  
* **Database Migration Engine:** Alembic

### **2.3 AI Orchestration & Engines**

* **Agentic Frameworks:** LangGraph (For stateful, multi-agent checkout loops), LangChain  
* **LLM Foundations:** OpenAI (GPT-4o models), Gemini (Gemini 1.5 Pro/Flash via Google AI Studio)  
* **Interoperability:** Model Context Protocol (MCP) Support

### **2.4 Data, Cache & Queue Infrastructure**

* **Primary Relational Database:** PostgreSQL  
* **Caching & Session State Store:** Redis  
* **Asynchronous Task Queue:** Celery

### **2.5 Infrastructure & Containerization**

* **Containerization Engine:** Docker  
* **Multi-Container Orchestration:** Docker Compose  
* **Reverse Proxy & Web Server:** Nginx

## **3\. Project Folder Structure**

The repository enforces an absolute separation of concerns. The backend follows a combination of the **Service Layer Pattern** and **Repository Pattern**, completely decoupling data access from business business logic.

Plaintext  
project-root/  
├── frontend/  
│   ├── public/  
│   └── src/  
│       ├── assets/         \# Static imagery, global SVGs  
│       ├── components/     \# Atomic reusable UI inputs, buttons, tables  
│       ├── constants/      \# Enums, strict platform arrays, system messages  
│       ├── hooks/          \# Custom hooks (useAuth, useSession, useCart)  
│       ├── layouts/        \# DashboardLayout, AuthLayout, StorefrontLayout  
│       ├── pages/          \# Login, Register, CoreDashboard, Inventory, Analytics  
│       ├── routes/         \# PrivateRoute and PublicRoute component declarations  
│       ├── services/       \# Base Axios instances, API communication modules  
│       ├── store/          \# Context API or lightweight state hooks  
│       ├── styles/         \# global.css with Tailwind directives  
│       ├── types/          \# Strict TypeScript interface declarations  
│       └── utils/          \# Formatting tools, token decoders, validation tools  
├── backend/  
│   ├── app/  
│   │   ├── api/            \# API versioning routes v1 (auth, merchants, items)  
│   │   ├── models/         \# SQLAlchemy 2.0 domain entity models  
│   │   ├── schemas/        \# Pydantic v2 validation data schemas  
│   │   ├── services/       \# Core business logic processing layer  
│   │   ├── repositories/   \# Raw async SQL data interactions (CRUD)  
│   │   ├── middleware/     \# Auth checks, CORS rules, logging, rate limits  
│   │   ├── core/           \# Security configs, JWT decoders, base settings  
│   │   ├── agents/         \# LangGraph state configurations and model routing  
│   │   ├── prompts/        \# Localized Amharic/English LLM system instructions  
│   │   ├── tasks/          \# Celery background jobs (Image uploads, messaging queues)  
│   │   └── utils/          \# Date formatters, security salts, logging setup  
│   ├── tests/              \# Pytest modules  
│   └── migrations/         \# Alembic environment and version upgrade states  
├── docker/                 \# Production/Development Dockerfiles  
│   ├── frontend.Dockerfile  
│   ├── backend.Dockerfile  
│   └── nginx.conf  
├── docs/                   \# Full markdown API contract snapshots  
├── scripts/                \# Database seeding, deployment controls, backup macros  
└── docker-compose.yml

## **4\. Environment Variables**

Every layer of the system must remain highly configurable. Under no circumstances are hardcoded credentials or system endpoints permitted within the repository codebase.

Ini, TOML  
\# \==============================================================================  
\# SaleOS Master Environment Variables Configuration Block  
\# \==============================================================================

\# Core Application Directives  
APP\_NAME\=SaleOS  
APP\_ENV\=production  
SECRET\_KEY\=super\_secret\_cryptographic\_signing\_key\_do\_not\_leak\_0911  
FRONTEND\_URL\=https://app.saleos.com  
BACKEND\_URL\=https://api.saleos.com

\# Core Security / JWT Token Properties  
JWT\_SECRET\=jwt\_token\_encryption\_and\_validation\_secret\_key\_hash\_8899  
JWT\_EXPIRE\_MINUTES\=60

\# Distributed Infrastructure Access Parameters  
DATABASE\_URL\=postgresql+asyncpg://saleos\_admin:secure\_db\_pass\_2026@postgres\_host:5432/saleos\_db  
REDIS\_URL\=redis://redis\_host:6379/0

\# Artificial Intelligence Engine Routing API Credentials  
OPENAI\_API\_KEY\=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  
GEMINI\_API\_KEY\=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

\# Dedicated Microservice Communication Access Endpoints  
TELEGRAM\_SERVICE\_URL\=http://telegram\_service:8001  
TIKTOK\_SERVICE\_URL\=http://tiktok\_service:8002  
INSTAGRAM\_SERVICE\_URL\=http://instagram\_service:8003  
FACEBOOK\_SERVICE\_URL\=http://facebook\_service:8004  
YOUTUBE\_SERVICE\_URL\=http://youtube\_service:8005

\# Proprietary External Core OCR Interface Routing  
EXTERNAL\_ETHIOPIAN\_BANK\_OCR\_API\_URL\=https://ocr.internal.platform/api/v1/verify-receipt  
EXTERNAL\_ETHIOPIAN\_BANK\_OCR\_API\_TOKEN\=ocr\_secure\_handshake\_bearer\_token\_abc123

\# Institutional SMTP Transaction Email Directives  
SMTP\_HOST\=smtp.mailgun.org  
SMTP\_PORT\=587  
SMTP\_USERNAME\=notifications@transactional.saleos.com  
SMTP\_PASSWORD\=mailgun\_auth\_password\_string\_secure

## **5\. Coding Standards**

### **5.1 Backend Infrastructure (FastAPI / Python)**

* **Strict Type Hints:** Every function parameter, class property, and return type must state its explicit python type annotation (e.g., async def get\_by\_id(id: UUID) \-\> models.Merchant | None:).  
* **Mandatory Async Execution:** All network operations, database executions, and service inter-communication pathways must use asynchronous signatures (async/await). Avoid blocking calls (time.sleep or synchronous requests) to preserve process scalability.  
* **Decoupled Architectural Separation:** Controllers handles route inputs and schemas $\\rightarrow$ Service Layer handles multi-entity business coordination $\\rightarrow$ Repository handles database reads/writes via execution blocks.  
* **SOLID Principles Execution:** Every class or module must retain a single responsibility. Interfaces must remain isolated, and components should depend on abstractions rather than rigid implementations.

### **5.2 Frontend Engineering Standards (React / TS)**

* **Functional Composition:** Zero class components are permitted. Use modern functional components with clear typed props (export const OrderTable: React.FC\<OrderTableProps\> \= ({ orders }) \=\> { ... }).  
* **Strict TypeScript Interface Control:** Avoid the usage of any. Define custom strict types, schemas, and structural representations for every API data response and payload interface.  
* **Reusable Layout Component Extraction:** Repeated layout architectures, entry tables, and forms must be cleanly extracted into modular subcomponents located in src/components/ to maintain codebase hygiene.  
* **Separation of Styling Properties:** All display properties must use explicit utilities via Tailwind CSS. Inline styling blocks are explicitly forbidden.

### **Single Architecture Clarification Question**

Before I generate the massive database model mappings, entity-relationship models, full multi-tenant authorization matrix, and complete endpoint specs (Sections 6 through 12\) for **SaleOS**:  
When a merchant is registering a user account inside the main dashboard, will your SaaS support an **individual merchant multi-user hierarchy**? For instance, when a retail vendor signs up, do they need to invite their own internal employees and give them distinct permission boundaries (e.g., the owner is an *Admin*, while their sales staff are *Staff* roles with restricted views), or will each merchant operate via a single unified account?  
Once you verify this permission layer, I will map out the database schemas and authentication pathways to match your operational model.

### **6\. Database Requirements**

To support the multi-tenant, multi-user hierarchy, the SaleOS core database architecture utilizes composite logical grouping via explicit scoping keys. All entity tables live within the primary PostgreSQL database instance. Every table containing operational business data must enforce strict relational indexing on merchant\_id to maintain strict tenant isolation.

#### **6.1 Table: merchants**

* **Purpose:** Stores the core corporate root identities for businesses utilizing the platform.  
* **Columns:**  
  * id (UUID, PRIMARY KEY, Default: uuid\_generate\_v4())  
  * business\_name (VARCHAR(255), NOT NULL)  
  * contact\_phone (VARCHAR(20), NOT NULL, UNIQUE)  
  * contact\_email (VARCHAR(255), NOT NULL, UNIQUE)  
  * is\_active (BOOLEAN, Default: TRUE)  
  * created\_at (TIMESTAMP WITH TIME ZONE, Default: NOW())  
  * updated\_at (TIMESTAMP WITH TIME ZONE, Default: NOW())  
* **Constraints:** Unique constraints on email and phone.  
* **Indexes:** B-Tree index on id.

#### **6.2 Table: users**

* **Purpose:** Stores identity credentials and master profile information for all human operators across all permission tiers.  
* **Columns:**  
  * id (UUID, PRIMARY KEY, Default: uuid\_generate\_v4())  
  * merchant\_id (UUID, FOREIGN KEY matching merchants.id, NULLABLE for Super Admins)  
  * email (VARCHAR(255), NOT NULL, UNIQUE)  
  * password\_hash (TEXT, NOT NULL)  
  * first\_name (VARCHAR(100), NOT NULL)  
  * last\_name (VARCHAR(100), NOT NULL)  
  * phone\_number (VARCHAR(20), NOT NULL, UNIQUE)  
  * role (VARCHAR(50), NOT NULL) — Evaluates strictly to: SUPER\_ADMIN, ADMIN, MANAGER, STAFF, CUSTOMER.  
  * is\_verified (BOOLEAN, Default: FALSE)  
  * mfa\_secret (VARCHAR(128), NULLABLE)  
  * mfa\_enabled (BOOLEAN, Default: FALSE)  
  * created\_at (TIMESTAMP WITH TIME ZONE, Default: NOW())  
  * updated\_at (TIMESTAMP WITH TIME ZONE, Default: NOW())  
* **Constraints:** Foreign key cascading deletion on merchant\_id.  
* **Indexes:** Composite B-Tree index on (merchant\_id, id), single index on email.

#### **6.3 Table: products**

* **Purpose:** Holds the centralized canonical definitions of items available for sale across all omnichannel points of distribution.  
* **Columns:**  
  * id (UUID, PRIMARY KEY, Default: uuid\_generate\_v4())  
  * merchant\_id (UUID, FOREIGN KEY matching merchants.id, NOT NULL)  
  * title (VARCHAR(255), NOT NULL)  
  * description (TEXT, NULLABLE)  
  * base\_price (NUMERIC(12, 2), NOT NULL)  
  * sku (VARCHAR(100), NOT NULL)  
  * image\_urls (TEXT\[\], Default: '{}')  
  * created\_at (TIMESTAMP WITH TIME ZONE, Default: NOW())  
  * updated\_at (TIMESTAMP WITH TIME ZONE, Default: NOW())  
* **Constraints:** Composite Unique constraint on (merchant\_id, sku).  
* **Indexes:** B-Tree index on merchant\_id, Hash index on sku.

#### **6.4 Table: inventory\_ledger**

* **Purpose:** Coordinates real-time, atomic allocation of stock availability to eliminate race conditions between channels.  
* **Columns:**  
  * id (UUID, PRIMARY KEY, Default: uuid\_generate\_v4())  
  * product\_id (UUID, FOREIGN KEY matching products.id, NOT NULL)  
  * merchant\_id (UUID, FOREIGN KEY matching merchants.id, NOT NULL)  
  * quantity (INT, NOT NULL, Constraint: quantity \>= 0)  
  * reserved\_quantity (INT, Default: 0, Constraint: reserved\_quantity \>= 0)  
  * location\_label (VARCHAR(100), Default: 'Central Warehouse')  
* **Constraints:** Foreign Key cascades down from products and merchants. Check constraints prevent inventory drops below absolute zero.  
* **Indexes:** Unique Index on product\_id.

#### **6.5 Table: orders**

* **Purpose:** Tracks processing, channel origin, and state metrics for checkouts.  
* **Columns:**  
  * id (UUID, PRIMARY KEY, Default: uuid\_generate\_v4())  
  * merchant\_id (UUID, FOREIGN KEY matching merchants.id, NOT NULL)  
  * customer\_id (UUID, FOREIGN KEY matching users.id, NULLABLE if transaction originates anonymously)  
  * channel\_source (VARCHAR(50), NOT NULL) — Evaluates to: TELEGRAM, TIKTOK, FACEBOOK, INSTAGRAM, YOUTUBE, WEB\_STORE.  
  * channel\_order\_reference (VARCHAR(100), NULLABLE)  
  * total\_amount (NUMERIC(12, 2), NOT NULL)  
  * order\_status (VARCHAR(50), Default: 'PENDING') — Statuses: PENDING, PROCESSING, PAID, PENDING\_MANUAL\_REVIEW, FULFILLED, CANCELLED.  
  * created\_at (TIMESTAMP WITH TIME ZONE, Default: NOW())  
* **Indexes:** B-Tree indexes on merchant\_id, order\_status, and channel\_source.

## **7\. Entity Relationship (ER) Diagram Specification**

Plaintext  
\+-------------------+           \+-------------------+  
|     MERCHANTS     |           |       USERS       |  
\+-------------------+           \+-------------------+  
| id (PK)           |1       1..\*| id (PK)           |  
| business\_name     |-----------| merchant\_id (FK)  |  
| contact\_phone     |           | email             |  
| contact\_email     |           | password\_hash     |  
\+-------------------+           | role              |  
          |                     \+-------------------+  
          | 1                             | 1  
          |                               |  
          | 1..\* | 0..\*  
\+-------------------+           \+-------------------+  
|     PRODUCTS      |           |      ORDERS       |  
\+-------------------+           \+-------------------+  
| id (PK)           |1          | id (PK)           |  
| merchant\_id (FK)  |--+        | merchant\_id (FK)  |  
| title             |  |        | customer\_id (FK)  |  
| base\_price        |  |        | channel\_source    |  
| sku               |  |        | total\_amount      |  
\+-------------------+  |        | order\_status      |  
          | 1          |        \+-------------------+  
          |            |  
          | 1          | 1..\*  
\+-------------------+  |  
| INVENTORY\_LEDGER  |  |  
\+-------------------+  |  
| id (PK)           |  |  
| product\_id (FK)   |--+  
| merchant\_id (FK)  |  
| quantity          |  
\+-------------------+

* **Merchants to Users:** One-to-Many ($1 \\rightarrow \\text{\*}$). A singular root Merchant profile owns multiple allocated user profiles (Admins, Managers, Staff).  
* **Merchants to Products:** One-to-Many ($1 \\rightarrow \\text{\*}$). Products are wholly contained within specific merchant partitions.  
* **Products to Inventory Ledger:** One-to-One ($1 \\rightarrow 1$). Each individual product maps directly to a physical inventory ledger baseline to lock stock state updates.  
* **Merchants to Orders:** One-to-Many ($1 \\rightarrow \\text{\*}$). Inbound multi-channel requests populate centralized merchant transaction tables.

## **8\. API Specification (Core Auth Contracts)**

### **8.1 Merchant Authentication Token Request**

* **Endpoint:** POST /api/v1/auth/login  
* **Content-Type:** application/json

**Request Payload:**

JSON  
{  
  "email": "admin@ethiopiancoffee.com",  
  "password": "SecurePassword123\!"  
}

**Success Response (HTTP 200 OK):**

JSON  
{  
  "access\_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5YjFk...",  
  "token\_type": "bearer",  
  "expires\_in\_seconds": 3600,  
  "user": {  
    "id": "c1a6b01b-c744-4f81-9b16-5b430856aa72",  
    "first\_name": "Bereket",  
    "last\_name": "Sewnet",  
    "email": "admin@ethiopiancoffee.com",  
    "role": "ADMIN",  
    "merchant\_id": "4ea63b4b-8899-4c12-bda4-1b11782bb04c"  
  }  
}

**Error Response (HTTP 401 Unauthorized):**

JSON  
{  
  "detail": "Invalid credentials provided. Verify operational email status and password values."  
}

## **9\. Authentication Flow Requirements**

The identity management system requires absolute enforcement of session integrity across all microservice entry endpoints.

* **Login:** Processes user verification against Argon2 or bcrypt password hashing schemes, issuing standard short-lived JWT signatures.  
* **Register:** Allows new root merchant creation alongside an initialized user identity containing the ADMIN role scope.  
* **Refresh Token:** Rotates an secure HTTP-Only cookie-based refresh payload to extend administrative dashboard activity without exposing credentials.  
* **Logout:** Inactivates the ongoing JWT configuration record signature by registering the token signature on an internal distributed Redis block list until expiry.  
* **Forgot / Reset Password:** Standard secure loop deploying signed verification configurations via SMTP channels to safely rewrite account credentials.  
* **Email Verification:** Mandates activation verification steps before clearing an account to change system structures or access channel automation parameters.  
* **Multi-Factor Authentication (MFA):** Implements time-based OTP processing checks using software keys (authenticator apps) for roles containing root administrative privileges (SUPER\_ADMIN, ADMIN).

## **10\. Authorization & Permissions Matrix**

Authorization is tightly managed at the route controller and service layer via functional interceptors reading active JWT identity scope claims.

| Platform Operational Capability | Super Admin | Admin (Owner) | Manager | Staff | Customer |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Modify Global System Billing / Tiers | **YES** | NO | NO | NO | NO |
| Provision / Revoke Merchant Microservices | **YES** | NO | NO | NO | NO |
| Configure Core Merchant System Settings | NO | **YES** | NO | NO | NO |
| Invite Internal Business Users & Manage Roles | NO | **YES** | **YES** | NO | NO |
| Modify Base Product & Inventory Entities | NO | **YES** | **YES** | **YES** | NO |
| Force Manual Override on OCR Pending Review | NO | **YES** | **YES** | NO | NO |
| Review Standard Order Logs & Analytics Tables | NO | **YES** | **YES** | **YES** | NO |
| Initiate Manual Cross-Platform Publishing Posts | NO | **YES** | **YES** | **YES** | NO |
| Query Individual Storefront Purchases / Profile | NO | NO | NO | NO | **YES** |

## **11\. Core Interface UI Requirements**

### **11.1 Master Dashboard Consolidation View**

* **Purpose:** Serves as the high-level cockpit detailing real-time sales velocity, live channel health markers, and critical operational notifications.  
* **Interface Components:**  
  * **Metric Aggregation Rows:** Interactive structural widgets summarizing gross multi-channel sales volume in ETB, ongoing active orders, and transaction processing state queues.  
  * **Unified Activity Pipeline:** List containing incoming social interactions requiring active evaluation or automated processing metrics.  
  * **Action Triggers & Inputs:** Fast action controls enabling immediate transition to manual cross-platform broadcasting panels or inventory editing views.  
  * **Validation Frameworks:** Structural form protections implemented via React Hook Form and Zod to lock date filters, string inputs, and export scopes to exact validation formats.

## **12\. UX Engineering Standards**

* **Adaptive Device Scaling:** Fluid layout distribution guarantees zero visual artifact clutter across compact mobile viewports, tablet configurations, or high-resolution workspace displays.  
* **Accessibility Directives:** Absolute alignment with WCAG AA compliance benchmarks across contrast structures, structural focus frameworks, and descriptive structural labeling parameters.  
* **Transient UI Processing States:** Implements predictive skeleton loading blocks during long-running background queries to avoid layout shifts. Clear processing states flag active, completed, or failed background automation pipeline events.


This is the complete Software Requirements Specification (SRS) for the **SaleOS Telegram Microservice**.  
To meet your critical requirement for dynamic, UI-driven configuration, we must employ a **Dynamic Bot Manager Architecture**. Because SaleOS is multi-tenant, you cannot hardcode a merchant's Telegram Bot Token in the .env file (otherwise, changing it would require a server restart and would break other merchants' bots).  
Instead, the .env file will hold *infrastructure* secrets, while the database will securely store individual *merchant configurations* (like their specific bot tokens and custom auto-reply texts). The UI will update the database via the FastAPI backend, which will dynamically mount or dismount that merchant's Telegram bot webhook at runtime.

# **Software Requirements Specification (SRS)**

## **Module: SaleOS Telegram Microservice**

## **1\. Microservice Overview**

* **Microservice Name:** SaleOS-Telegram  
* **Architecture Role:** Standalone asynchronous messaging worker and custom UI dashboard.  
* **Core Objective:** To seamlessly connect merchant Telegram bots to the centralized SaleOS core. It processes real-time webhooks, manages conversational AI state, executes interactive inline-keyboard checkouts, and routes local payment screenshot uploads to the core OCR verification engine.  
* **Dynamic Capability:** Merchants can configure bot tokens, localized Amharic response templates, and activation statuses dynamically through the React dashboard without requiring developer intervention or service reboots.

## **2\. Mandatory Tech Stack**

### **2.1 Frontend (Standalone UI/UX)**

* **Framework:** Vite \+ React \+ TypeScript (Strict Mode)  
* **Styling & UI:** TailwindCSS \+ Shadcn UI  
* **State & Forms:** React Query, React Hook Form, Zod

### **2.2 Backend API & Bot Engine**

* **Framework:** FastAPI (Python 3.12+)  
* **Bot Library:** aiogram (3.x) — The most robust, fully asynchronous Python Telegram bot framework. It natively integrates with FastAPI and Redis for high-concurrency webhook processing.  
* **LLM Integration:** LangChain / OpenAI / Gemini (Imported from core for intent parsing).

### **2.3 Data Infrastructure**

* **Relational Database:** PostgreSQL (Connecting to the shared master SaleOS database).  
* **State Management (FSM):** Redis (To track exactly where a user is in the checkout flow).

## **3\. Dynamic Configuration Strategy (UI vs. .env)**

### **3.1 Infrastructure Config (.env \- Server Level)**

These values are strictly for the server environment and never change per merchant.

Ini, TOML  
APP\_NAME\=SaleOS-Telegram  
APP\_PORT\=8001  
ENVIRONMENT\=production  
MASTER\_DB\_URL\=postgresql+asyncpg://user:pass@host:5432/saleos\_db  
REDIS\_URL\=redis://redis\_host:6379/1  
CORE\_PLATFORM\_API\_URL\=https://api.saleos.com  
TELEGRAM\_WEBHOOK\_BASE\_DOMAIN\=https://telegram.saleos.com

### **3.2 Dynamic Merchant Config (UI Level)**

When a merchant uses the React frontend to update their bot, the UI hits an API endpoint. The backend saves the new configuration to the database and immediately calls the Telegram API (setWebhook) dynamically using the new token.

## **4\. Database Requirements (Telegram Schema)**

These tables live inside the master database but are strictly scoped to the Telegram microservice operations.

#### **4.1 Table: telegram\_bot\_configs**

* **Purpose:** Stores the dynamically changeable bot credentials and UI configurations for each merchant.  
* **Columns:**  
  * id (UUID, PRIMARY KEY)  
  * merchant\_id (UUID, FOREIGN KEY matching merchants.id, UNIQUE)  
  * bot\_token (VARCHAR(255), NOT NULL, UNIQUE) — *Set via the React UI.*  
  * bot\_username (VARCHAR(100), NULLABLE)  
  * welcome\_message (TEXT, Default: 'Welcome to our store\! How can we help you?')  
  * is\_active (BOOLEAN, Default: FALSE)  
  * updated\_at (TIMESTAMP)

#### **4.2 Table: telegram\_customers**

* **Purpose:** Maps native Telegram users to the core SaleOS ecosystem.  
* **Columns:**  
  * id (UUID, PRIMARY KEY)  
  * merchant\_id (UUID, FOREIGN KEY matching merchants.id)  
  * telegram\_user\_id (BIGINT, NOT NULL)  
  * chat\_id (BIGINT, NOT NULL)  
  * username (VARCHAR(255), NULLABLE)  
  * first\_name (VARCHAR(255), NULLABLE)  
* **Constraints:** Composite Unique on (merchant\_id, telegram\_user\_id).

#### **4.3 Table: telegram\_chat\_sessions**

* **Purpose:** Logs conversational memory for the AI agent to maintain context.  
* **Columns:**  
  * id (UUID, PRIMARY KEY)  
  * customer\_id (UUID, FOREIGN KEY matching telegram\_customers.id)  
  * redis\_fsm\_state (VARCHAR(100), NULLABLE) — Tracks states like AWAITING\_PAYMENT\_RECEIPT.  
  * last\_interaction (TIMESTAMP)

## **5\. API Specification**

### **5.1 Internal Dashboard APIs (React UI to Backend)**

**1\. Update Bot Configuration**

* **Endpoint:** PUT /api/v1/telegram/config  
* **Auth:** JWT Required (Admin/Manager role)  
* **Request Payload:**

JSON  
{  
  "bot\_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",  
  "welcome\_message": "Selam\! Choose an item below to buy.",  
  "is\_active": true  
}

* **Backend Action:** Saves to telegram\_bot\_configs, dynamically unregisters the old webhook, and registers the new webhook with Telegram servers via aiogram.

### **5.2 External Telegram Webhook API (Telegram to Backend)**

**1\. Main Webhook Listener**

* **Endpoint:** POST /api/v1/telegram/webhook/{merchant\_id}  
* **Purpose:** Receives all live chat updates, button clicks, and photo uploads from Telegram.  
* **Process:**  
  1. Validates the webhook payload.  
  2. Pushes the update to the aiogram Dispatcher instance mapped to that specific merchant\_id.  
  3. Executes the asynchronous conversational logic.

## **6\. UI/UX Requirements (React Dashboard)**

### **6.1 Layout & Navigation**

* **Sidebar Menu:** Dashboard, Bot Settings, Broadcast Message, Live Chats, Order Fallbacks.

### **6.2 Bot Settings Page (The Dynamic Config UI)**

* **Inputs:**  
  * Bot Token (Password field with eye toggle to hide/show).  
  * Welcome Message (Rich text area for Amharic/English).  
  * Status Toggle (Switch component: Online / Offline).  
* **Validation:** Zod validates the bot token format (must match Telegram's \[0-9\]+:\[a-zA-Z0-9\_-\]+ regex) before submitting via Axios.  
* **Feedback:** Toast notification confirming "Bot successfully connected and webhook mounted."

### **6.3 Manual Broadcast Page**

* **Purpose:** Allows merchants to push a single message to all users who have started their bot.  
* **Inputs:**  
  * Image/Video Uploader.  
  * Caption text box.  
  * "Send to All" or "Filter by past buyers" selection.  
* **Action:** Triggers a Celery background task on the FastAPI backend to loop through telegram\_customers and dispatch send\_photo payloads via aiogram, respecting Telegram's bulk messaging rate limits.

## **7\. Operational Workflows & Agent Logic**

### **7.1 The Chat-to-Checkout Pipeline**

1. **Trigger:** Customer types "I want the Nike shoes."  
2. **AI Parsing:** Backend passes text to the LangChain router, which identifies "purchase intent" and queries the shared database products table.  
3. **Inline UI:** Bot replies using Telegram Inline Keyboards displaying product details, a generated photo, and a "Buy via Telebirr" button.  
4. **FSM Lock:** Redis updates the user's state to AWAITING\_PAYMENT\_RECEIPT.

### **7.2 The OCR Payment Fallback Loop (Critical Path)**

1. **Action:** User uploads a screenshot image.  
2. **Download:** The FastAPI backend downloads the image directly from Telegram servers into memory buffers (no disk I/O to maintain speed).  
3. **Verification Request:** Backend fires the image buffer to the external Ethiopian Bank OCR API.  
4. **Logic Split:**  
   * **Success:** Update master orders and inventory\_ledger. Bot replies: *"Payment verified\! Order \#123 is confirmed."*  
   * **Failure/Blurry:** Redis FSM retains the AWAITING\_PAYMENT\_RECEIPT state. Bot replies: *"We couldn't read that receipt automatically. We notified our team for manual review."* A WebSocket event pushes an alert directly to the React UI dashboard for human intervention.
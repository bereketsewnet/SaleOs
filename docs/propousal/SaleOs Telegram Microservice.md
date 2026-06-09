# **Section 2: Microservice Architecture Breakdown**

## **2.1 The Telegram Microservice**

The Telegram microservice is a standalone, fully containerized backend application designed to handle high-concurrency messaging, e-commerce checkouts, and channel broadcasting. Because Telegram acts as the primary digital storefront for millions of Ethiopian users, this service is heavily optimized for fast webhook processing, interactive UI elements (Inline Keyboards), and localized payment flows.

### **2.1.1 Frontend UI/UX (Strict API Separation)**

Following a strict API-first architecture, the standalone Telegram dashboard contains **zero business logic**. It is a lightweight frontend (e.g., React or Next.js) that purely consumes the Telegram Microservice REST API.

* **Dashboard Capabilities:** Merchants can view live bot conversations, intervene manually in chats, configure auto-reply logic, and view transaction ledgers.  
* **Auth & Integration Readiness:** The frontend authenticates via JWT. When the Centralized Hub is deployed, this exact UI can be embedded as a module or accessed via SSO, requiring no rewriting of the frontend code.

### **2.1.2 Automated Customer Replies & Checkout Flow**

The core of the microservice is an event-driven conversational agent that listens to Telegram webhooks in real-time.

* **Intent Parsing:** When a user messages the merchant’s bot (e.g., *"Sint no?"* or *"Do you have this in size M?"*), the backend webhook listener parses the intent using the Centralized AI Engine and replies instantly, maintaining session memory via Redis.  
* **Interactive Cart:** The bot utilizes Telegram’s **Inline Keyboards** to allow users to select sizes, colors, and delivery zones natively within the chat without typing.

### **2.1.3 Automated & Manual Content Posting**

The service manages broadcasting to Telegram Channels and Groups:

* **Manual Posting:** The merchant uploads an image/video and types a caption in the dashboard. The frontend hits the /api/telegram/broadcast endpoint, and the backend uses the Telegram sendPhoto or sendMessage API to push the content to the merchant's public channel.  
* **AI-Assisted Automated Posting:** The merchant prompts the system (e.g., *"Generate a promotional post for my new Nike shoes"*). The Centralized AI Engine generates the copy, and the **Telegram Adaptor** automatically formats it specifically for Telegram—applying bolding \<b\>, italics \<i\>, and appending an inline "Buy Now" button before pushing it live.

### **2.1.4 External OCR Payment Verification & Fallback Workflow**

Because Telegram does not natively support Ethiopian local payment gateways seamlessly, this microservice uses a custom computer vision checkout loop integrated with the external OCR API.  
**The Payment State Machine:**

1. **Trigger:** The customer clicks "Checkout with Telebirr/CBE Birr" via an Inline Keyboard.  
2. **Prompt:** The bot replies: *"Please transfer \[Amount\] ETB to account 1000123456 and upload the screenshot receipt here."*  
3. **OCR Processing:** The user uploads the image. The Telegram webhook catches the photo object, downloads the image to a secure temporary buffer, and makes a highly secure server-to-server HTTP POST request to the **External Ethiopian Bank OCR API**.  
4. **Resolution (Success Path):** The OCR returns {"status": "success", "amount": 1200, "tx\_id": "FT12345XYZ"}. The backend verifies the amount matches the cart total, updates the master database inventory, and replies: *"Payment verified\! Your order is scheduled for delivery."*  
5. **Resolution (Fallback Path):** If the OCR API fails, times out, or detects a manipulated image, the system triggers the **Graceful Fallback Protocol**:  
   * The database flags the order status as PENDING\_MANUAL\_REVIEW.  
   * A real-time WebSocket alert triggers on the merchant's UI dashboard.  
   * The bot automatically replies to the user: *"I am currently unable to automatically verify your payment screenshot. Your order is safely saved\! Please contact our human support at 0911-XX-XX-XX or wait for a representative to message you shortly."*

### **2.1.5 Database Independence & Syncing**

While the tables live in the shared centralized database instance, the Telegram module operates strictly within its designated schema (e.g., telegram\_users, telegram\_sessions, telegram\_campaigns).

* All queries are scoped with WHERE Merchant\_ID \= ?.  
* When a checkout completes, the microservice executes an atomic SQL transaction to decrement the master inventory\_ledger table, ensuring TikTok and Facebook cannot sell the same item.
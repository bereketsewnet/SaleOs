This is the **Software Requirements Specification (SRS) for the SaleOS-Instagram Microservice**. Consistent with your architecture, this service leverages the **Instagram Graph API** to manage professional interactions, emphasizing high-throughput webhook handling and strict adherence to Meta’s rate-limiting constraints.

# **Software Requirements Specification (SRS)**

## **Module: SaleOS-Instagram Microservice**

## **1\. Microservice Overview**

* **Microservice Name:** SaleOS-Instagram  
* **Architecture Role:** Asynchronous media publishing, DM automation, and "Comment-to-DM" conversion.  
* **Core Objective:** To manage Instagram Professional accounts, automate lead capture from Reels/Posts, and maintain a seamless transition from public engagement to private checkout.  
* **Dynamic Capability:** Merchants connect their Instagram Professional accounts via Facebook OAuth. The system maintains long-lived tokens and provides a visual dashboard to toggle auto-replies, manage media assets, and view engagement analytics.

## **2\. Mandatory Tech Stack**

### **2.1 Frontend (Standalone UI/UX)**

* **Framework:** Vite \+ React \+ TypeScript.  
* **Styling:** Shadcn UI for real-time dashboards and asset management grids.  
* **Real-time UX:** React Query to poll for comment updates or WebSocket hooks for live "Message Received" notifications.

### **2.2 Backend & Instagram Integration**

* **Framework:** FastAPI (Python 3.12+).  
* **Integration Library:** Meta Graph API (Instagram for Business).  
* **Worker System:** Celery (task queuing for media publishing/transcoding) \+ Redis (rate-limiting tracker).

## **3\. Dynamic Configuration & Auth**

### **3.1 OAuth & Token Lifecycle**

* **Flow:** OAuth via Meta Developer App (Facebook Login → Page Selection → Instagram Business Account selection).  
* **Token Management:** The microservice stores encrypted tokens in instagram\_bot\_configs.  
* **Dynamic Refresh:** An internal background job monitors token expiration (60 days) and triggers automatic refresh requests to Meta, ensuring uninterrupted service.

## **4\. Database Requirements (Instagram Schema)**

#### **4.1 Table: instagram\_bot\_configs**

* **Purpose:** Stores per-merchant account metadata and automation triggers.  
* **Columns:**  
  * merchant\_id (UUID, FOREIGN KEY, UNIQUE)  
  * ig\_user\_id (VARCHAR(255), UNIQUE)  
  * access\_token (TEXT, Encrypted)  
  * is\_automated (BOOLEAN, Default: TRUE)  
  * dm\_trigger\_keywords (JSONB) — *List of keywords (e.g., "price", "link") that trigger auto-DMs.*

#### **4.2 Table: instagram\_engagement**

* **Purpose:** Tracks interactions to prevent duplicate automated replies.  
* **Columns:**  
  * id (UUID, PRIMARY KEY)  
  * ig\_comment\_id (VARCHAR(255), UNIQUE)  
  * user\_id (VARCHAR(255))  
  * status (VARCHAR(50)) — *Status: REPLIED, DM\_SENT, PROCESSED.*

## **5\. API Specification**

### **5.1 Internal Dashboard APIs**

* POST /api/v1/instagram/publish: Accepts images/Reels, generates a media container, and publishes.  
* **GET /api/v1/instagram/metrics**: Fetches engagement insights (reach, saves, shares).  
* **PUT /api/v1/instagram/config**: Updates automation settings (keywords, auto-reply text).

### **5.2 External Meta Webhook**

* **POST /api/v1/instagram/webhook/{merchant\_id}**: Listens for mentions, comments, and messages.  
  * *Logic:*  
    1. Validates the event type.  
    2. Filters for business logic (e.g., "Does the comment contain a trigger keyword?").  
    3. Pushes the task to the **Central AI Core** for intent parsing.  
    4. Dispatches the reply via Graph API.

## **6\. UI/UX Requirements (React Dashboard)**

* **Account Health Dashboard:** Displays "Connection Status" and "API Quota Usage" (a gauge showing the current hour’s request count).  
* **Comment Monitor:** A smart feed that highlights comments requiring attention versus those already handled by the bot.  
* **Content Studio:** A robust media uploader with aspect-ratio validation (4:5 to 1.91:1 for feed, 9:16 for Reels) to ensure compliance with API requirements before upload.  
* **Automation Playground:** A "Test" feature where a merchant can input a string and see exactly how the AI would respond based on their current custom configuration.

## **7\. Rate-Limiting & Compliance (Critical)**

* **The 200/Hour Limit:** The microservice implements a **Redis-based Sliding Window Rate Limiter**. Every API call made by a merchant’s token is logged in Redis. If the count reaches 180, the backend queues all remaining messages and alerts the UI dashboard with an "Optimizing flow to avoid API blocks" warning.  
* **24-Hour Messaging Window:** The AI agent is restricted by logic: if a user hasn't engaged within 24 hours, the messages endpoint will be bypassed, and the system will prompt the merchant to send an "Human-Verified" notification instead.
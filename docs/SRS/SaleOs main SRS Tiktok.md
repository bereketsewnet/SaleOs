This is the **Software Requirements Specification (SRS) for the SaleOS-TikTok Microservice**.  
Following your requirement, this microservice is built with the same architecture: **FastAPI (Backend)**, **Vite/React/TypeScript (Frontend)**, and a **Dynamic Configuration Management** system that allows merchants to link their TikTok business accounts via OAuth and manage automation logic without hardcoding.

# **Software Requirements Specification (SRS)**

## **Module: SaleOS-TikTok Microservice**

## **1\. Microservice Overview**

* **Microservice Name:** SaleOS-TikTok  
* **Architecture Role:** Asynchronous video engagement, automated DM conversion, and comment-to-inbox routing.  
* **Core Objective:** Monitor official TikTok business activity, convert public video engagement into private sales threads, and facilitate automated content distribution across multiple platforms.  
* **Dynamic Capability:** Merchants link their TikTok Business profiles via OAuth 2.0. The microservice manages the token lifecycle, handles comment-to-DM webhooks, and provides a centralized video-asset management panel.

## **2\. Mandatory Tech Stack**

### **2.1 Frontend (Standalone UI/UX)**

* **Framework:** Vite \+ React \+ TypeScript (Strict Mode).  
* **Components:** Shadcn UI data tables for tracking comments; media-upload drag-and-drop zones for video/image assets.  
* **API Communication:** Axios with interceptors for automatic JWT handling.

### **2.2 Backend & TikTok Integration**

* **Framework:** FastAPI (Python 3.12+).  
* **Integration Library:** Official **TikTok for Developers API** (Content Posting API, Business Messaging API).  
* **Async Workflow:** httpx for non-blocking API calls to TikTok’s endpoints; Celery for background processing of video uploads.

### **2.3 Data Infrastructure**

* **Shared Database:** PostgreSQL (Integrated into master SaleOS database).  
* **Queue:** Redis (Queueing comment-to-DM triggers to stay under rate limits).

## **3\. Dynamic Configuration & Auth**

### **3.1 OAuth Lifecycle Management**

Instead of simple API tokens, TikTok requires **OAuth 2.0**.

* **Flow:** The React UI triggers an OAuth redirect to TikTok. Upon successful authorization, TikTok returns an auth\_code. The FastAPI backend exchanges this for an access\_token and refresh\_token.  
* **Storage:** These tokens are stored encrypted in the tiktok\_bot\_configs table. The backend handles automatic token refreshing before every API request to ensure the merchant’s account never disconnects.

## **4\. Database Requirements (TikTok Schema)**

#### **4.1 Table: tiktok\_bot\_configs**

* **Purpose:** Stores per-merchant OAuth credentials and account status.  
* **Columns:**  
  * id (UUID, PRIMARY KEY)  
  * merchant\_id (UUID, FOREIGN KEY, UNIQUE)  
  * tiktok\_business\_id (VARCHAR(255))  
  * access\_token (TEXT, Encrypted)  
  * refresh\_token (TEXT, Encrypted)  
  * token\_expires\_at (TIMESTAMP)  
  * is\_connected (BOOLEAN, Default: FALSE)

#### **4.2 Table: tiktok\_comments**

* **Purpose:** Logs public interactions to enable AI reply tracking.  
* **Columns:**  
  * id (UUID, PRIMARY KEY)  
  * comment\_id (VARCHAR(255), UNIQUE)  
  * video\_id (VARCHAR(255))  
  * user\_name (VARCHAR(255))  
  * text (TEXT)  
  * status (VARCHAR(50)) — *Status: PENDING, REPLIED, DM\_SENT.*

## **5\. API Specification**

### **5.1 Internal Dashboard APIs**

* **POST /api/v1/tiktok/auth/connect**: Initiates the OAuth redirect.  
* **POST /api/v1/tiktok/publish**: Accepts video binary and description, then dispatches to TikTok Content Posting API.  
* **GET /api/v1/tiktok/comments**: Fetches the latest comments for the dashboard UI.

### **5.2 External TikTok Webhook**

* **POST /api/v1/tiktok/webhook/{merchant\_id}**: Listens for comment.create events.  
  * *Logic:* Triggers the **Central AI Core** to generate a reply, then fires two parallel tasks:  
    1. A public reply on the video.  
    2. A private DM trigger if the merchant has "Comment-to-DM" enabled.

## **6\. UI/UX Requirements (React Dashboard)**

* **Account Connection Panel:** A "Connect TikTok Business" button that initiates the OAuth flow.  
* **Video Publisher:** A multi-platform form allowing the merchant to upload a video, set a caption, and choose to publish simultaneously to TikTok, Instagram, and Facebook.  
* **Engagement Monitor:** A table displaying comments from all videos, with an "Action" column showing status: \[Auto-Replied\], \[DM Sent\], or \[Manual Action Required\].  
* **Validation:** Zod schemas to ensure video duration does not exceed the limit and caption length stays within the character count before the API call is ever made.

## **7\. Operational Workflow (The "Viral Engagement" Loop)**

1. **Ingestion:** A customer comments on a viral video. The TikTok webhook triggers the microservice.  
2. **AI Orchestration:** The backend calls the **Central AI Core**. The AI checks if the product mentioned is in stock via the master inventory\_ledger.  
3. **Public Reply:** The microservice sends a public comment: *"We have that in stock\! DM sent."*  
4. **Private DM:** The microservice executes the Business Messaging API call to initiate a DM to the customer.  
5. **Checkout Transition:** The user receives a message with the SaleOS checkout link. Once the user uploads the payment receipt, the **OCR Verification Loop** (integrated from Core) confirms the transaction and triggers the order-fulfillment state.

**Architectural Warning:** TikTok’s API is highly sensitive to rapid-fire actions. To prevent account bans, this microservice uses a **Distributed Rate-Limiter (Redis)** that ensures we never exceed TikTok's 200 DM-per-hour limit per account, even if a post goes viral and receives 5,000 comments in one minute.
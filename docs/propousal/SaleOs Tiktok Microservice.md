# **Section 2: Microservice Architecture Breakdown (Continued)**

## **2.2 The TikTok Microservice**

The TikTok microservice is an independent, highly responsive service optimized for video-centric customer conversion and viral content engagement. Because TikTok operates at a high velocity with intense traffic spikes, this microservice focuses on asynchronous processing queues, automated comment-to-DM conversions via the official **TikTok Business Messaging API**, and strict media asset validation layers.

### **2.2.1 Frontend UI/UX (Strict API Separation)**

The dedicated TikTok sub-dashboard provides merchants with a video management suite, real-time comment feeds, and DM tracking metrics.

* **Dashboard Capabilities:** Merchants can review comments handled by the AI agent, view analytics on video performance, monitor active direct message funnels, and link their official business profiles via OAuth.  
* **Auth & Integration Readiness:** Built purely as a consumer of the standalone backend REST API, the interface relies completely on JWT bearer authentication. It is built to seamlessly drop into the Centralized Web Hub UI layout.

### **2.2.2 Automated Customer Replies: The Comment-to-DM Loop**

TikTok users interact predominantly through public comment sections under short-form videos. The microservice uses an event-driven webhook worker to capture these interactions instantly and turn them into closed sales.

\[Customer Comments on Video\] ──\> (TikTok Webhook) ──\> \[TikTok Microservice Backend\]  
                                                               │  
                                                       (Central AI Core)  
                                                               │  
                                                               ▼  
\[Direct Message Opened & Sent\] \<── (Business Messaging API) \<──┴──\> \[Public Comment Reply Posted\]

* **The Webhook Listener:** The backend exposes a secure HTTPS endpoint (/api/webhooks/tiktok) registered on the TikTok Developer Portal to listen for comment.create events.  
* **The Public Reply Workflow:** When a customer comments (e.g., *"Sint no? bota ale?"* or *"Price please"*), the backend passes the text to the Central AI Core. The system checks the database inventory and triggers a public reply: *"Hi\! It's 1,200 ETB. We just slid into your private DMs with ordering details\! 📥"*  
* **The Private DM Trigger:** Simultaneously, using the biz.messaging scope, the service opens a direct conversation with the commenter’s user\_id. The agent sends a personalized opening message referencing the product in the video, prompting the buyer to initiate a conversational checkout.

### **2.2.3 Automated & Manual Content Posting (Gated Video Assets)**

To accommodate TikTok's architecture, the microservice enforces strict structural boundaries on content publishing using the official **TikTok Content Posting API**.

* **Manual Multi-Platform Posting:** When triggered by the Centralized Web Hub, the microservice accepts video uploads and captions. The frontend sends these multi-part form data assets to the /api/tiktok/publish endpoint, which securely posts the video and descriptive metadata to the merchant’s profile.  
* **AI-Assisted Automated Posting (Strict Gating):** If a merchant prompts the AI to auto-generate a post for TikTok, the system executes a strict validation layer:  
  * **The Gating Rule:** The system blocks execution if no base video asset is attached. The UI displays an alert: *"TikTok requires a video asset. The AI can generate your text descriptions, hashtags, and titles, but you must upload a base video to proceed."*  
  * **The Image Exception:** If the merchant selects an image-based post, the microservice formats the collection specifically as a **TikTok Image Carousel Post**, generating trending hashtags and structured descriptions via the Central AI Core before deploying.

### **2.2.4 External OCR Payment Verification Integration**

Once the AI conversational agent drives the TikTok customer from a comment into the direct message inbox, the transaction moves directly into the unified payment loop.

1. **The Call to Action:** The automated DM agent sends the payment breakdown and says: *"Please upload your Telebirr or bank transfer receipt screenshot here."*  
2. **The Direct Processing:** When the user uploads an image, the microservice catches the binary data through the messaging webhook, handles temporary cloud storage buffering, and hits your standalone **External Ethiopian Bank OCR API**.  
3. **The Success Flow:** Upon receiving transaction validation matching the exact cart parameters, the microservice updates the shared database schema, logs the transaction ID, and marks the item as ready for immediate delivery.  
4. **The Robust Fallback Protocol:** If the customer uploads a blurred photo or a duplicate transaction ID, the system:  
   * Flags the transaction status as PENDING\_MANUAL\_REVIEW.  
   * Pushes an immediate notification alert directly to the merchant’s TikTok dashboard UI.  
   * Automatically replies to the user: *"We couldn't verify this screenshot automatically. We have saved your cart\! Please call our support line or wait for a representative to check it manually."*

### **2.2.5 Database Isolation & Concurrency Control**

* **Data Scoping:** All operations run strictly within separate TikTok domain tables (tiktok\_comments, tiktok\_dm\_sessions, tiktok\_video\_metadata) explicitly mapped to the master database via Merchant\_ID.  
* **Spike Handling:** To protect against intense database connection locking when a merchant's video goes viral and thousands of users comment simultaneously, the backend utilizes an asynchronous task queue (e.g., Redis with BullMQ or Celery) to rate-limit outbound public replies and serialize database writes safely.
# **Section 2: Microservice Architecture Breakdown (Continued)**

## **2.4 The Facebook Microservice**

The Facebook microservice is a standalone system tailored explicitly for Facebook Pages (commercial and brand profiles). It handles heavy comment-to-inbox customer conversions via the official **Meta Graph API** and **Messenger Platform**. Since a single viral post or promotional campaign can generate thousands of concurrent engagements, this microservice relies heavily on background task workers, asynchronous processing queues, and robust payload normalization logic.

### **2.4.1 Frontend UI/UX (Strict API Separation)**

The standalone Facebook microservice sub-dashboard provides a dedicated web console for page management, tracking metrics, and administrative control.

* **Dashboard Capabilities:** Merchants can review automated comment replies, monitor active direct messaging checkouts, view an analytical activity feed of page posts, and securely hook their brand pages to the system via Meta OAuth.  
* **Auth & Integration Readiness:** The frontend serves purely as a visual consumer of the underlying REST API, relying entirely on JWT security claims. It is structured to instantly plug into the layout of the Centralized Web Hub.

### **2.4.2 Automated Customer Replies: The "Feed-to-Messenger" Pipeline**

Facebook users rely heavily on commenting on public Page posts to learn about inventory availability and pricing. The microservice tracks these engagements in real-time by listening to Meta's unified **Feed Webhooks** rather than relying on heavy polling loops.

\[User Comments on Page Post\] ──\> (Meta Webhook: field: "feed") ──\> \[Facebook Backend Router\]  
                                                                        │  
                                                                 (Central AI Core)  
                                                                        │  
                                                                        ▼  
\[Private Messenger Chat Initiated via Comment ID\] \<── (Graph API) \<─────┴──\> \[Public Comment Reply Posted\]

* **The Webhook Listener:** The backend exposes a secure HTTPS endpoint (/api/webhooks/facebook) subscribing to the feed object on the Page level. When a user posts a comment, Meta issues an instant JSON POST payload containing the parent post metadata, the text content, and a unique comment\_id.  
* **The Public Reply Action:** The microservice hands the text over to the Central AI Core to parse user intent (e.g., assessing expressions like *"Price?"* or *"Addis Ababa bota ale?"*). Once the response text is formulated, the backend sends a POST request to /{comment\_id}/comments to notify the buyer publicly: *"Check your Messenger inbox\! We've sent you the pricing and ordering link."*  
* **The Private Inbox Escalation (The Private Reply):** Simultaneously, to transition the customer into a secure checkout environment, the microservice calls Meta's /messages endpoint. Meta allows apps to open an automated inbox thread *by passing the specific comment\_id as the recipient identifier*. Once the user responds to this first DM, the official 24-hour conversational window unlocks for full AI transactional interaction.

### **2.4.3 Automated & Manual Content Posting**

The microservice handles publishing textual updates, high-resolution media collections, and video assets to the Facebook Page's public feed.

* **Manual Multi-Platform Publishing:** When triggered via the Centralized Hub, the backend processes media uploads and description metadata. It issues multipart form-data requests directly to the Facebook Page's feed endpoint (/{page\_id}/feed or /{page\_id}/photos), immediately pushing the content live to the merchant's timeline.  
* **AI-Assisted Automated Posting:** When a merchant inputs a simple prompt to generate content, the Centralized AI Engine drafts the marketing copy and generates images. The **Facebook Adaptor** strips unsupported markdown syntax, maps relevant emoticons, and structures the text blocks into high-performing page post formats before instructing the backend to publish.

### **2.4.4 External OCR Payment Verification Integration**

When an automated Messenger chat progresses to final billing, the microservice relies on its hardwired link to your independent payment processing engine.

1. **The Request:** The AI agent provides the merchant's Telebirr or CBE account numbers and states: *"Please send your payment transfer screenshot right here to lock in your delivery."*  
2. **The Processing:** The user uploads their receipt. The webhook catches the Messenger attachment event, down-buffers the image securely, and forwards it instantly via an authorized server-to-server call to your **External Ethiopian Bank OCR API**.  
3. **The Success Automation:** If the OCR service extracts valid receipt text matching the expected cart value and confirms an unused Transaction ID, the backend pushes a ledger transaction to the shared database, locks the inventory row, and prints a success notification back to the buyer's screen.  
4. **The Robust Fallback Protocol:** If the uploaded receipt is cropped, unreadable, or a duplicate transaction ID attempt, the system:  
   * Automatically changes the order billing status to PENDING\_MANUAL\_REVIEW.  
   * Dispatches a live, real-time alert to the merchant's Facebook dashboard interface via WebSockets.  
   * Adjusts the chatbot narrative to reassure the customer: *"We are experiencing a small delay verifying this receipt automatically. We have safely saved your cart items\! Please call us directly or hold tight while our team manually reviews your transaction."*

### **2.4.5 Database Isolation & Meta Platform Constraints**

* **Data Scoping:** All operations are tightly confined to the specific Facebook space tables (facebook\_page\_meta, facebook\_chat\_sessions, facebook\_feed\_logs), structured via Merchant\_ID to preserve tenant privacy inside the shared centralized database core.  
* **Meta Compliance & Queueing:** Meta enforces strict token lifetimes and rate-limiting margins (the 24-hour messaging policy rule). To protect the platform against API rate violations or lost webhooks during high-concurrency traffic loops, the microservice handles all transactional outbound messages inside an asynchronous message queue (such as Redis backed by BullMQ or Celery) to carefully regulate the rate of API calls.

How does this look for the Facebook architecture? If you find this design robust and aligned
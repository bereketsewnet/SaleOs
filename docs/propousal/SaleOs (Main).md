# **Section 1: Executive Summary & System Architecture Topology**

## **1.1 Executive Summary**

The **Omnichannel Social Commerce & Automation Hub** is an enterprise-grade SaaS platform designed to centralize, automate, and scale e-commerce operations for merchants across Ethiopia and the broader African market. The system bridges the gap between fragmented social media engagement and structured e-commerce by providing intelligent conversational agents, automated cross-platform content publishing, and instantaneous local payment verification.  
Built on an API-first, modular architecture, the platform empowers merchants to seamlessly operate across the five dominant digital channels—**Telegram, TikTok, Instagram, Facebook, and YouTube**. Merchants can adopt the entire suite through a Centralized Web Dashboard or subscribe exclusively to individual channel microservices.  
By natively integrating a specialized Optical Character Recognition (OCR) API to instantly verify Ethiopian digital bank transfers (e.g., Telebirr, CBE Birr) directly within the social chat flows, the platform solves the region's most critical e-commerce bottleneck: manual payment fraud and fulfillment delays.

## **1.2 Core System Capabilities**

1. **Omnichannel Auto-Replies:** Intelligent, LLM-powered conversational agents capable of handling customer inquiries, stock checks, and checkout flows directly inside social media direct messages and comment sections.  
2. **AI-Assisted & Manual Content Publishing:** A unified publishing engine that allows merchants to manually upload or AI-generate localized marketing content (text, images, and video metadata) and distribute it simultaneously across all selected social platforms.  
3. **Automated Payment Verification:** Direct integration with a proprietary external OCR engine to instantly parse, verify, and approve customer payment screenshot receipts during the chat checkout process.  
4. **Centralized E-Commerce Storefront:** A fully functional, web-based e-commerce storefront dynamically synced with the merchant's social media inventory, acting as the ultimate destination for complex orders.

## **1.3 System Architecture Topology**

The platform utilizes a **Modular Shared-Database Architecture**, balancing the strict logical isolation of microservices with the transactional safety required for real-time inventory management.

### **1.3.1 The Centralized Database Core**

To ensure absolute inventory integrity and prevent overselling across different platforms, all microservices connect to a single, highly available database instance.

* **Logical Data Isolation:** Every database table strictly enforces a Merchant\_ID foreign key relationship. This guarantees absolute data privacy and isolates the operational data of a merchant who uses a single microservice from one who uses the entire hub.  
* **Atomic Inventory Sync:** If an item is purchased via the Telegram bot, the database transaction instantly updates the master inventory ledger, immediately reflecting the out-of-stock status on the Facebook bot and the Central E-Commerce website.

### **1.3.2 The Microservices Ecosystem**

The system is divided into five distinct, API-driven backend microservices. Each service maintains its own dedicated UI, backend logic, and API gateways, ensuring a merchant can utilize them independently.

* **Telegram Service:** Handles inline keyboards, group management, and Telegram-specific bot flows.  
* **TikTok Service:** Integrates with the TikTok Business API for video comment replies and DM transitions.  
* **Instagram Service:** Manages Instagram Graph API interactions, grid post publishing, and Story/DM automation.  
* **Facebook Service:** Manages Messenger API checkouts and Facebook Page feed publishing.  
* **YouTube Service:** Handles YouTube Data API connections, specifically gating automation behind strict video-asset validation rules for Shorts and standard uploads.

### **1.3.3 The Centralized Web Hub & SSO**

The Master Dashboard acts as the platform's control center.

* **Dynamic Single Sign-On (SSO):** Merchants authenticate via JSON Web Tokens (JWT). The JWT payload carries the merchant’s specific subscription claims, allowing the central UI to dynamically render only the dashboards and features for the microservices they have purchased.  
* **Centralized AI Generation Engine:** Instead of duplicating AI logic, the Hub houses a central AI Engine. When a merchant requests an automatic post, the core LLM generates the baseline marketing asset and passes it through **Platform-Specific Adaptors** (e.g., adding hashtags for Instagram, formatting bold text for Telegram) before dispatching it to the respective microservices.

### **1.3.4 External OCR API Integration & Fallback Loop**

Every conversational microservice is hardwired to connect securely with the external Ethiopian Bank OCR service during the checkout phase.

* **The Happy Path:** Customer uploads a Telebirr screenshot $\\rightarrow$ Microservice sends image to OCR API $\\rightarrow$ API returns verified amount and Transaction ID $\\rightarrow$ Microservice marks order as paid and notifies merchant.  
* **The Fallback Path:** If the OCR API returns an "unreadable" or "failed" flag, the microservice gracefully degrades. It instantly logs the transaction as PENDING\_MANUAL\_REVIEW on the merchant's dashboard and auto-replies to the customer with manual support contact information, ensuring no sale is lost to technical failure.
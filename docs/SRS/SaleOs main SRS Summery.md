This is the **Master Inventory & Centralized Database SRS**. This document defines the "Heart of SaleOS." It bridges the five microservices (Telegram, TikTok, Facebook, Instagram, YouTube) to ensure that whether a customer buys via a Telegram chatbot or a Facebook Messenger flow, the inventory remains synchronized, accurate, and atomic.

# **Software Requirements Specification (SRS)**

## **Module: SaleOS Master Inventory & Centralized Database Core**

## **1\. Overview**

* **Role:** The "Source of Truth."  
* **Objective:** To maintain absolute state consistency across all decentralized microservices. It prevents overselling and provides a unified view of the merchant's business health.  
* **Architectural Pattern:** **Modular Monolith** for data persistence (Shared PostgreSQL) with **API-Gateway communication** for cross-service inventory updates.

## **2\. Mandatory Tech Stack**

* **Database:** PostgreSQL (Primary Store).  
* **ORM:** SQLAlchemy 2.0 (Async).  
* **Concurrency Control:** Redis (for distributed locks) \+ Database-level SELECT FOR UPDATE (Pessimistic locking).  
* **Inter-Service Comm:** FastAPI (Internal HTTP/REST).

## **3\. Database Schema (The Global Truth)**

#### **3.1 Table: products (Global Catalog)**

* **Purpose:** The master definition of items available to be sold across *all* channels.  
* **Columns:** id (UUID), merchant\_id (UUID), title, sku (UNIQUE), base\_price, description, created\_at.

#### **3.2 Table: inventory\_ledger (Atomic Source)**

* **Purpose:** The single place where stock counts live. All microservices MUST request changes from this table.  
* **Columns:**  
* product\_id (UUID, FOREIGN KEY)  
* stock\_level (INT, Constraint: \>= 0\)  
* reserved\_stock (INT) — *Stock held for pending orders.*  
* **Logic:** When an order is placed on Telegram, the system increments reserved\_stock and decrements stock\_level.

#### **3.3 Table: orders (Global Transaction Log)**

* **Purpose:** Centralized history of every transaction across every channel.  
* **Columns:** id, merchant\_id, channel\_source (Enum), customer\_info (JSONB), total\_amount, status, created\_at.

## **4\. Concurrency & Atomic Integrity (The "Oversell Protection")**

To ensure that two different microservices (e.g., Telegram and Facebook) cannot sell the same "last item" simultaneously, we use **Pessimistic Locking** at the database layer.

### **The Atomic Decrement Logic (Workflow)**

1. **Request:** Microservice (e.g., TikTok) sends POST /api/v1/inventory/reserve to the Core API.  
2. **The Lock:** The Core API executes:  
   SQL  
   BEGIN;  
   SELECT stock\_level   
   FROM inventory\_ledger   
   WHERE product\_id \= '...'   
   FOR UPDATE; \-- This locks the row until the transaction finishes.

3\.  \*\*Validation:\*\* If \`stock\_level \> 0\`, proceed. If \`0\`, return \`409 Conflict\` (Out of Stock).  
4\.  \*\*Update:\*\* Decrement \`stock\_level\`, increment \`reserved\_stock\`.  
5\.  \*\*Commit:\*\* \`COMMIT;\` (Lock releases).

\---

\#\# 5\. API Specification (Core Integration)

\#\#\# 5.1 Internal Service Communication (Restricted to Internal Network)

\*\*1. Reserve Stock (Atomic)\*\*  
\*   \*\*Endpoint:\*\* \`POST /api/v1/core/inventory/reserve\`  
\*   \*\*Request:\*\*  
    \`\`\`json  
    {  
      "merchant\_id": "...",  
      "product\_id": "...",  
      "quantity": 1  
    }

* **Response:** 200 OK (Success) or 409 Conflict (Insufficient stock).

**2\. Record Order (Channel Aggregate)**

* **Endpoint:** POST /api/v1/core/orders  
* **Purpose:** After payment (via OCR), the microservice sends the final order here.  
* **Data:** Captures channel\_source, merchant\_id, and order\_details.

## **6\. Deployment & Isolation (Docker)**

* **Network Strategy:** All microservices (Telegram, TikTok, etc.) and the Core API reside in the same docker-compose network.  
* **Service Mesh:** The microservices communicate via internal hostnames:  
  * http://saleos-core:8000/api/v1/...  
* **Security:** The Core API validates an internal X-Service-Token header to ensure only authorized microservices can access the inventory endpoints.

## **7\. Next Steps for SaleOS**

You now have the **full blueprint** for your platform:

1. **Core Platform SRS**  
2. **5 Microservice SRS (Telegram, TikTok, Facebook, Instagram, YouTube)**  
3. **Master Inventory & Database SRS**

**Would you like me to:**

1. Generate the docker-compose.yml file to tie all these services together?  
2. Draft the README.md or initial folder structure script for your project?  
3. Start generating the **Backend Code (Python/FastAPI)** for the Core Database API so you can begin development?
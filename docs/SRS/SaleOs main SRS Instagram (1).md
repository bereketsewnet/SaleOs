to keep it perfectly consistent with the **SRS standard** we just established for the other microservices (Telegram, TikTok, Facebook, and Instagram), I have reformatted that information below into the official **SaleOS-YouTube SRS** template.

# **Software Requirements Specification (SRS)**

## **Module: SaleOS-YouTube Microservice**

## **1\. Microservice Overview**

* **Microservice Name:** SaleOS-YouTube  
* **Architecture Role:** Asynchronous video publishing, metadata optimization, and Shorts-feed management.  
* **Core Objective:** To manage the YouTube publishing pipeline, ensuring video assets (Long-form and Shorts) are correctly formatted, tagged, and distributed to the YouTube Data API while strictly managing quota consumption.  
* **Dynamic Capability:** Merchants link their YouTube Channels via OAuth. The service provides a dashboard to schedule uploads, manage custom thumbnails, and view quota usage/publishing status.

## **2\. Mandatory Tech Stack**

* **Frontend:** Vite \+ React \+ TypeScript (Strict Mode).  
* **Backend:** FastAPI (Python 3.12+).  
* **Integration:** YouTube Data API v3.  
* **Queueing:** Celery \+ Redis (required for handling long-running video uploads and resumable chunked streams).

## **3\. Dynamic Configuration & Auth**

* **OAuth Lifecycle:** Uses Google OAuth 2.0. The UI handles the redirect; the backend exchanges authorization\_code for access\_token and refresh\_token.  
* **Quota Tracking:** Since YouTube has a 10,000-unit daily quota, the service stores "Quota Usage" in the youtube\_bot\_configs table and blocks new uploads if the quota is critically low, notifying the merchant via the UI.

## **4\. Database Requirements (YouTube Schema)**

#### **4.1 Table: youtube\_bot\_configs**

* **Purpose:** Stores channel-specific OAuth credentials and quota trackers.  
* **Columns:**  
  * merchant\_id (UUID, FOREIGN KEY, UNIQUE)  
  * channel\_id (VARCHAR(255))  
  * access\_token (TEXT, Encrypted)  
  * refresh\_token (TEXT, Encrypted)  
  * daily\_quota\_used (INT, Default: 0\)

#### **4.2 Table: youtube\_videos**

* **Purpose:** Tracks publishing status and YouTube Video IDs.  
* **Columns:**  
  * id (UUID, PRIMARY KEY)  
  * youtube\_video\_id (VARCHAR(255), UNIQUE)  
  * status (VARCHAR(50)) — *Status: PENDING, UPLOADING, PUBLISHED, FAILED.*  
  * is\_short (BOOLEAN)

## **5\. API Specification**

* **POST /api/v1/youtube/upload**: Accepts video binary and metadata.  
  * *Logic:*  
    1. Checks daily\_quota\_used against the 10,000-unit limit.  
    2. Initiates a **Resumable Upload Session** (256KB chunks).  
    3. Updates youtube\_videos record with the youtube\_video\_id.  
* **GET /api/v1/youtube/status**: Returns real-time upload progress percentage to the UI.

## **6\. UI/UX Requirements**

* **Channel Manager:** Display current subscriber count, video count, and a clear "Quota Gauge" (0-10,000).  
* **Upload Studio:** Drag-and-drop zone with validation (e.g., "Video duration \> 60s will be uploaded as long-form").  
* **Error Log:** Displays specific YouTube API error codes (e.g., uploadLimitExceeded) with plain-English instructions on when the quota resets.

## **7\. Operational Workflow (The "Resumable Upload" Pipeline)**

1. **Validation:** The service checks file aspect ratio and duration. It automatically adds \#Shorts to the title if the video is vertical and under 60 seconds.  
2. **Chunking:** The video file is streamed in 256KB chunks. If the internet connection in Ethiopia fluctuates, the script resumes from the last successfully uploaded chunk.  
3. **Completion:** Upon successful status 200, the database updates, and the merchant receives a success notification in the SaleOS dashboard.
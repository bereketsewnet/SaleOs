# **YouTube Automation System: Project Requirements Document (PRD)**

## **1\. System Architecture Overview**

The system follows a decoupled, event-driven pipeline. It monitors a cloud storage directory (e.g., Google Drive or AWS S3), processes video assets, attaches dynamically generated metadata, and ships them to YouTube.

\[Cloud Storage Trigger\]   
       │  
       ▼  
\[n8n Workflow Engine\] ──(Validation: Duration/Aspect Ratio)  
       │  
       ▼  
\[Media Processor / Unified API\] ──(OAuth Token Management)  
       │  
       ▼  
\[YouTube Data API v3 / Shorts Shelf\]

## **2\. Technical Specifications & Requirements**

### **Video & Formats Check**

To guarantee that the YouTube algorithm correctly routes the content (especially for the Shorts feed), incoming media must pass strict structural constraints:

| Content Type | Aspect Ratio | Maximum Duration | Target Audio Level | Required Meta Signals |
| :---- | :---- | :---- | :---- | :---- |
| **YouTube Shorts** | **9:16** (1080×1920) | $\\le 60 \\text{ seconds}$ | \-14 LUFS (AAC Codec) | \#Shorts string in title/desc |
| **Long-form Video** | **16:9** (1920×1080) | No hard limit | \-14 LUFS | Custom Thumbnail (Max 2MB) |

### **Native API Quota Bottlenecks (2026 Constraints)**

The **YouTube Data API v3** enforces a strict daily token economy that requires defensive engineering:

* **Default Daily Quota:** 10,000 units per Google Cloud Project.  
* **Cost per Video Upload (**videos.insert**):** **1,600 units** (\~6 uploads per day total across the project before hitting a hard ceiling).  
* **Cost per Thumbnail Upload:** 50 units.  
* **Cost per Status Check (videos.list):** 1 unit per poll.  
* **Mitigation Strategy:** The application will implement an internal database to track upload states rather than polling YouTube aggressively. For large-scale multi-channel deployment, we will utilize external unified posting APIs (e.g., *Blotato*, *Upload-Post*, or *PostPeer*) which handle OAuth pools and abstract the quota constraints away from our local server infrastructure.

## **3\. Core Workflow Engine (Procedural Step-by-Step)**

The automation logic is built inside a resilient step sequence to prevent silent failures, token expiration, or formatting rejections.

**1.Ingestion & Change Monitoring:**Instant Trigger.  
The n8n workflow monitors the dedicated cloud storage folder. When a raw .mp4 or .mov payload drops, the system locks the file state and extracts raw file metrics using an inline metadata node.

**2.Asset Validation & Conditioning:**Automated Gatekeeper.  
Run programmatic checks on file criteria. If aspect ratio is vertical and duration is less than 60 seconds, flag the payload internally as IS\_SHORTS \= true. Ensure the title string has the \#Shorts token attached to force-signal the Shorts shelf.

**3.OAuth 2.0 Auth Matrix:**Token Rotation.  
The system looks up the target channel's credentials. If using the native API, it extracts the stored refresh\_token from encrypted storage, requests a fresh, short-lived access\_token from Google's authorization endpoint, and signs the request.

**4.Resumable Upload Exec:**Chunked Payload Delivery.  
Initiate a multi-part resumable session via a POST request. Stream the video binary data to the resulting session URI in byte chunks multiplied by **256 KB**. If the connection drops mid-stream, query the URI range header and resume exactly from the last received byte without burning additional quota.

**5.Error Capture & Backoff:**Defensive Recovery.  
If the API returns a rate-limit error or quota exhaustion signal, catch the status code. The workflow pauses, triggers a notification to management, shifts the video into a Pending Queue, and applies an exponential backoff retry interval.

## **4\. Interactive Workflow Architecture Simulator**

Adjust the parameters below to calculate target data sizes, upload timing projections, and structural behaviors of the ingestion pipeline.
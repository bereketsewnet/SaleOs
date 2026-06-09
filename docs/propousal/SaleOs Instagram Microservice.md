## **1\. Rules & Constraints**

Meta enforces tight restrictions on automated messaging. Keeping your scripts or workflow nodes compliant requires adhering to these parameters:

* **The 24-Hour Messaging Window:** When a user interacts with your Instagram account (sends a DM, replies to a Story, or comments triggering an auto-DM), it opens a strict **24-hour window**. Inside this window, you can send unlimited messages, including promotional URLs or discount codes. Every user reply resets the 24-hour clock.  
* **The 200 DMs/Hour Rate Limit:** Your App’s automated DM rate limit is restricted to a maximum of **200 automated messages per hour, per connected Instagram account** on a rolling 60-minute window. If a post goes viral and triggers 500 actions simultaneously, your backend must queue or throttle the spikes to avoid dropping requests or triggering a temporary API suspension.  
* **The 1-DM-per-User-per-24H Limit:** For comment-to-DM triggers specifically, Meta limits automation to **1 automated DM per unique user every 24 hours**. Subsequent comment triggers from the same user within that day will be blocked by the API to prevent spam patterns.

## **2\. Handling Webhook Payloads**

Instead of polling endpoints, you should listen for real-time events. Ensure your publicly accessible HTTPS endpoint (or your workflow webhook node) responds with an HTTP status code 200 OK within **30 seconds**, or Meta will flag it as a timeout and attempt 5 retries with an incremental delay.

### **Inbound Comment Trigger Layout**

When a user drops a keyword under a post, Meta pushes a POST request to your webhook URL. This payload outlines how to track the comment\_id, the text string, and the user's specific scopes:

JSON  
{  
  "object": "instagram",  
  "entry": \[  
    {  
      "id": "17841412345678901",   
      "time": 1717637639,  
      "changes": \[  
        {  
          "field": "comments",  
          "value": {  
            "id": "17921188223456789",  
            "text": "Send me the link\!",  
            "media": {  
              "id": "17852100987654321",  
              "media\_product\_type": "REELS"  
            },  
            "from": {  
              "id": "6543210987",  
              "username": "ig\_traveler\_96"  
            }  
          }  
        }  
      \]  
    }  
  \]  
}

## **3\. Dispatching Responses**

To send an automated message back to the user, ensure you dispatch your POST request with the payload in the **Request Body**, not via query parameters. Placing fields like recipient in query strings will throw a (\#100) The parameter recipient is required exception.

### **Outbound Message Payload**

* **Endpoint:** \[https://graph.facebook.com/v22.0/me/messages\](https://graph.facebook.com/v22.0/me/messages)  
* **Headers:** Content-Type: application/json  
* **Query Param:** access\_token=YOUR\_PAGE\_ACCESS\_TOKEN

JSON  
{  
  "recipient": {  
    "id": "6543210987"  
  },  
  "message": {  
    "text": "Thanks for reaching out\! Here is the direct link you requested: https://example.com/portal"  
  }  
}

**Permission Checklist:** If you encounter a (\#200) App does not have Advanced Access... error during development, ensure your Meta App has been switched from Development to Live mode and has been granted full Advanced Access for both instagram\_basic and instagram\_manage\_messages via App Review.  
Where should we map out the logic next? We can design an automated queue to handle bursts that exceed the 200/hour limit, or configure the precise token exchange steps to get your 60-day long-lived Page Access Token.
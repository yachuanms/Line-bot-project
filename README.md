# LINE Secretary Chatbot  

A LINE chatbot that serves as a personal assistant by integrating restaurant recommendations, calendar reminders, and weather updates into one convenient platform.  

---

## Features  
- **Restaurant Recommendations**: Uses Google Maps API to suggest nearby popular restaurants.  
- **Schedule Reminders**: Syncs with Google Calendar API to provide daily reminders of important events.  
- **Weather Updates**: Sends daily morning weather notifications via a weather API.  
- **Convenience**: Interacts directly within LINE, no additional app installation required.  

---

## System Architecture  
- **Backend**: Flask server processes requests from the LINE Webhook.  
- **Tunnel**: Ngrok exposes the local server to the internet for LINE integration.  
- **External APIs**:  
  - Google Maps API  
  - Google Calendar API  
  - Weather API  

### Workflow  
1. User sends a message to LINE.  
2. LINE Webhook forwards the message to the Flask server.  
3. Flask processes the request, queries the appropriate API.  
4. Response is sent back to the user via LINE.  

---
# Contributors
- Hsu Ya-Chuan
- Hsu Hsuan-Kuang
- Lin Wen-Chen


# calendar_module.py
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Google Calendar 權限範圍
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def get_today_events():
    service = get_calendar_service()
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    end = (datetime.datetime.utcnow() + datetime.timedelta(hours=72)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    if not events:
        return "📅 沒有行程唷！"

    message = "📅 三天內行程如下：\n"
    for e in events:
        start_raw = e['start'].get('dateTime', e['start'].get('date'))

        # 處理時間格式
        try:
            dt = datetime.datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
            start_fmt = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            start_fmt = start_raw  # 全天事件，僅有日期

        summary = e.get('summary', '無標題')
        message += f"- {start_fmt}：{summary}\n"

    return message


if __name__ == '__main__':
    print("🔎 正在從 Google Calendar 擷取三天內行程...\n")
    events = get_today_events()
    print(events)
import re
import dateparser
from datetime import datetime, timedelta
import urllib.parse

def normalize_time_expression(time_str):
    # 替換中文時間詞為英文 AM/PM
    time_str = time_str.replace("上午", "AM").replace("早上", "AM")
    time_str = time_str.replace("中午", "PM").replace("下午", "PM").replace("晚上", "PM")

    # 處理「點半」成 30 分
    time_str = re.sub(r"(\d{1,2})點半", r"\1:30", time_str)
    # 處理「點」成整點
    time_str = re.sub(r"(\d{1,2})點", r"\1:00", time_str)

    # 加入 ":00" 結尾補強（避免「5月29日 下午2」這種）
    if re.match(r".*\d{1,2}$", time_str) and not re.search(r":\d{2}", time_str):
        time_str += ":00"

    from datetime import datetime
    this_year = datetime.now().year

    def month_num_to_en(month_num):
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_idx = int(month_num)
        if 1 <= month_idx <= 12:
            return months[month_idx - 1]
        return "May"  # 預設

    # 取代「X月Y日」為英文格式
    time_str = re.sub(r"(\d{1,2})月(\d{1,2})[日號]?",
                      lambda m: f"{month_num_to_en(m.group(1))} {int(m.group(2))}, {this_year}",
                      time_str)

    # 調整 PM/AM 的位置：將「PM2:00」 ➜ 「2:00 PM」
    time_str = re.sub(r"(AM|PM)(\d{1,2}:\d{2})", r"\2 \1", time_str)

    return time_str




def parse_event_from_text(text):
    original_text = text.strip()
    text = text.replace("新增行程", "").strip()

    # 擷取地點：「在XXX」
    location_match = re.search(r"在(\S+)", text)
    location = location_match.group(1) if location_match else ""

    # 擷取時間字串（如「7月3日13點」或「7月3日 下午1點」）
    time_pattern = re.search(
        r"((\d{4}年)?\d{1,2}[月/]\d{1,2}[日號]?\s*(上午|下午|晚上|中午)?\d{1,2}(點半|點|[:：]\d{2})?)",
        text
    )
    if time_pattern:
        raw_time_str = time_pattern.group(0)
        norm_time_str = normalize_time_expression(raw_time_str)
        print(f"🕵️ 偵測時間：{raw_time_str} ➜ 正規化後：{norm_time_str}")
        dt = dateparser.parse(norm_time_str, settings={
            'PREFER_DATES_FROM': 'future',
            'DATE_ORDER': 'YMD'
        }, languages=['en'])
        text = text.replace(raw_time_str, "")
        print(f"🕒 解析時間：{dt}")
    else:
        dt = None

    # 去掉地點片段
    if location:
        text = text.replace("在" + location, "")

    # 預設時間
    if not dt:
        print("⚠️ 無法解析時間，預設為今天下午2點")
        dt = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)

    # 活動標題與描述
    title = text.strip() if text.strip() else "行程提醒"
    description = original_text

    # 產生時間區段
    start_dt = dt
    end_dt = dt + timedelta(hours=2)

    # Google Calendar 格式
    gcal_time = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"

    return title, gcal_time, location, description, start_dt, end_dt

def create_gcal_url(title, gcal_time, location, description):
    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    return (
        f"{base_url}&text={urllib.parse.quote(title)}"
        f"&dates={gcal_time}&location={urllib.parse.quote(location)}"
        f"&details={urllib.parse.quote(description)}&openExternalBrowser=1"
    )


if __name__ == "__main__":
    input_text = "新增行程 6月4日 13:00 在中興大學 和璇光吃飯"
    title, gcal_time, location, description, start_dt, end_dt = parse_event_from_text(input_text)

    print("🔍 解析結果：")
    print("📌 標題：", title)
    print("🕒 時間區間：", gcal_time)
    print("📍 地點：", location)
    print("📝 描述：", description)
    print("📅 起始時間：", start_dt)
    print("📅 結束時間：", end_dt)

    gcal_url = create_gcal_url(title, gcal_time, location, description)
    print("🔗 Google 日曆連結：")
    print(gcal_url)


from flask import Flask, request, abort
from dotenv import load_dotenv
import os
from tools.event_parser import parse_event_from_text, create_gcal_url
from tools.calendar_module import get_today_events
from tools.weather import find_nearest_forecast_location, get_weather_weekly_forecast
from tools.AnswerBook import answer_book, daily_lucky
from tools.gemini_answer import gemini_recommend, gemini_translate
from tools.FindNearbyRestaurant import get_random_food, insert_food, delete_food,get_food, clear_food
from tools.FindNearbyRestaurant import find_nearby_restaurants, print_food_list, reset_food_list
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage, TemplateMessage,
    ConfirmTemplate, ButtonsTemplate, CarouselTemplate, CarouselColumn,
    MessageAction, PostbackAction, URIAction, MessagingApi, ImageMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, LocationMessageContent, PostbackEvent
from linebot.models.send_messages import ImageSendMessage

app = Flask(__name__)

load_dotenv()
configuration = Configuration(access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
api_client = ApiClient(configuration)
api = MessagingApi(api_client)

# 全域狀態變數
Weather_Func = False
Find_Restaurant = False
food = None
Random_Food = True

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    global Weather_Func, Find_Restaurant, food, Random_Food
    user_message = event.message.text.strip().lower()

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if any(keyword in user_message for keyword in ['拉麵', '牛肉麵', '壽司', '火鍋', '炒飯', '便當', '漢堡',
                                                       '披薩', '義大利麵', '健康餐', '炸雞', '燒烤', '小籠包', '餃子']) and "新增" not in user_message and "從清單刪除" not in user_message:
            food= user_message
            Find_Restaurant = True
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="『 + -> 位置資訊』發送您的位置")]
                )
            )
        elif "幫我找" in user_message and "餐廳" in user_message:
            print("找餐廳")
            food = user_message.replace(
                '幫我找', '').replace('餐廳', '').strip()
            Find_Restaurant = True
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="『 + -> 位置資訊』發送您的位置")]
                )
            )
        elif user_message == "查行程":
            reply = get_today_events()
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply)]
                )
            )

        elif user_message.startswith("新增行程"):
            #"新增行程 5月29日 13:00 or 下午1點 在台中中興大學吃飯"
            # 解析使用者輸入並建立 Google Calendar URL
            title, dates, location, description, start_dt, end_dt = parse_event_from_text(
                user_message)

            if dates:
                url = create_gcal_url(title, dates, location, description)
                messages = [
                    # TextMessage(text="📅 行程建立成功："),
                    TextMessage(
                        text=f"標題：{title}\n時間：{dates}\n地點：{location}\n描述：{description}"),
                    TextMessage(text=f"✅ 點我新增到 Google 行事曆：\n{url}")
                ]
            else:
                messages = [TextMessage(
                    text="❌ 無法解析時間，請確認格式，例如：新增行程 6月1日晚上7點在台大聚餐")]

            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages
                )
            )

        elif user_message == "天氣":
            Weather_Func = True
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="『 + -> 位置資訊』發送您的位置")]
                )
            )
            return

        elif user_message == "今天吃什麼":
            url = request.url_root.replace(
                "http", "https") + 'static/image.png'
            buttons_template = ButtonsTemplate(
                thumbnail_image_url=url,
                title='今天吃什麼',
                text='請選擇',
                actions=[
                    PostbackAction(label='我要轉盤來決定我今天吃什麼',
                                   data='action=random_food'),
                    PostbackAction(label="我要自己決定吃什麼",data = 'action=self_determine'),
                    PostbackAction(
                        label='我有幾個選項但不知道哪個好', data='action=chose_from_userlist'),
                ]
            )
            template_message = TemplateMessage(
                alt_text="功能選單",
                template=buttons_template
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[template_message]
                )
            )
        
        elif "新增" in user_message and "到清單" in user_message:
            
            food = user_message.replace(
                '新增', '').replace('到清單', '').strip()
            insert_food(food)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"已將 {food} 新增到清單\n目前清單為:\n{print_food_list()}")]
                )
            )
        elif "從清單刪除" in user_message:
            food = user_message.replace(
                '從清單刪除', '').strip()
            delete_food(food)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"已將 {food} 從清單刪除\n目前清單為:\n{print_food_list()}")]
                )
            )
        elif user_message == "運勢":
            # 隨機選擇一個運勢
            fortune = daily_lucky()
            if fortune == "大吉":
                image = "https://hsuhsulin.github.io/line_bot/good_luck/%E5%A4%A7%E5%90%89.png"
            elif fortune == "中吉":
                image = "https://hsuhsulin.github.io/line_bot/good_luck/%E4%B8%AD%E5%90%89.png"
            elif fortune == "小吉":
                image = "https://hsuhsulin.github.io/line_bot/good_luck/%E5%B0%8F%E5%90%89.png"
            elif fortune =="吉":
                image = "https://hsuhsulin.github.io/line_bot/good_luck/%E5%90%89.png"
            elif fortune == "凶":
                image = "https://hsuhsulin.github.io/line_bot/good_luck/%E5%A4%A7%E5%87%B6.png"
            elif fortune == "大凶":
                image = "https://hsuhsulin.github.io/line_bot/good_luck/%E5%A4%A7%E5%87%B6.png"
            elif fortune == "平":
                image = "https://hsuhsulin.github.io/line_bot/good_luck/%E5%B9%B3.png"
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=fortune),
                    ImageMessage(
                    original_content_url = image,
                    preview_image_url = image)]
                )
            )
        elif user_message == "解答之書":
            # 按下確定button 獲得答案
            confirm_message = TemplateMessage(
                alt_text="解答之書",
                template=ConfirmTemplate(
                    text="想好了沒? 好久喔!!!",
                    actions=[
                        PostbackAction(label="yes", data="action=anwer_book"),
                        PostbackAction(label="好了", data="action=anwer_book")
                    ]
                )
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(
                        text="如果你遇到無法做出決定的事情，可以讓答案之書在線幫你\n1.在心中默念一個具體的問題。\n2.閉上眼睛，集中注意力。\n3.輕輕點擊答案之書線上的書本。"), confirm_message]
                )
            )
            

        elif any(keyword in user_message for keyword in ["轉盤", "晚餐", "吃什麼", "隨機", "午餐"]):
            if Random_Food:
                food = get_random_food()
            else:
                food = get_food()
            url = request.url_root.replace(
                "http", "https") + 'static/card'
            columns = [
                CarouselColumn(
                    thumbnail_image_url=url+str(i+1)+'.png',
                    title=f'第{i+1}張卡牌',
                    text=f'這是第{i+1}張卡牌的描述',
                    actions=[PostbackAction(
                        label="翻開卡牌嗎?",data="action=turn"+str(i)+"-"+food)]
                ) for i in range(6)
            ]
            carousel_message = TemplateMessage(
                alt_text='這是 Carousel Template',
                template=CarouselTemplate(columns=columns)
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[carousel_message]
                )
            )

        elif user_message.startswith("翻譯"):
            response = gemini_translate(user_message)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)]
                )
            )


        else:
            # 使用 Gemini API 生成翻譯
            response = gemini_recommend(user_message)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)]
                )
            )

# 回傳到後台的東東繼續處理
@handler.add(PostbackEvent)
def handle_postback(event):
    global Weather_Func, Find_Restaurant, food, Random_Food
    data = event.postback.data
    reply_token = event.reply_token

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        if data == "action=self_determine":
            
            text = '請依照下面格式回傳:\n幫我找【請輸入關鍵字】餐廳\n例如:\n幫我找義大利麵餐廳'
        elif data == "action=chose_from_userlist":
            clear_food()
            Random_Food = False
            text = '請依照下面格式回傳:\n若要新增到食物清單 -> 新增【關鍵字】到清單\n若要刪除到食物清單 -> 從清單刪除【關鍵字】\n若要開始選擇 -> 轉盤'
        elif data == "action=random_food":
            Random_Food = True
            text = '輸入轉盤繼續'
        elif data == "action=anwer_book":
            # 隨機選擇一個運勢
            answer = answer_book()
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=answer)]
                )
            )
        elif "action=turn" in data:
            # 解析出卡牌編號和食物
            card_number, food = data.split("-")
            card_number = int(card_number.replace("action=turn", ""))
            food = food.replace(" ", "")
            text = f"第{card_number+1}張卡牌是{food}"
            confirm_message = TemplateMessage(
                alt_text="還要再轉一次嗎？",
                template=ConfirmTemplate(
                    text="還要再轉一次嗎？",
                    actions=[
                        MessageAction(label="是", text="轉盤"),
                        PostbackAction(label="否", data="action=find_restaurant")
                    ]
                )
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(
                        text=text), confirm_message]
                )
            )
        elif data == "action=find_restaurant":
            Find_Restaurant = True
            Random_Food = True
            reset_food_list()
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="為您查詢評分大於4.0的相關店家...\n『 + -> 位置資訊』發送您的位置")]
                )
            )
        message = TextMessage(type="text", text=text)
        api.reply_message(ReplyMessageRequest(
            reply_token=reply_token,
            messages=[message]
        ))
@handler.add(MessageEvent, message=LocationMessageContent)
def handle_location(event):
    global Weather_Func, Find_Restaurant, food, Random_Food

    lat = event.message.latitude
    lon = event.message.longitude
    messages = []

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        if Weather_Func:
            location_name = find_nearest_forecast_location(lat, lon)
            weather_info = get_weather_weekly_forecast(location_name)

            reply_lines = [
                f"📍 地點：{weather_info['location']}",
                f"\n【最高溫度 (°C)】{weather_info['max_temp']}",
                f"\n【最低溫度 (°C)】{weather_info['min_temp']}",
                f"\n【降雨機率 (%)】{weather_info['rain_prob']}",
                f"\n【紫外線指數】{weather_info['uvi']}",
                f"\n{weather_info['uvi_message']}",
                f"\n{weather_info['rain_message']}"
            ]

            reply_text = "\n".join(reply_lines)

            Weather_Func = False

            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

        if Find_Restaurant:
            dummy_response = "這是為您查詢的店家列表："
            restaurants = find_nearby_restaurants(
                lat, lon, radius=1000,
                API_KEY='AIzaSyAM0yh2cwd1jlmbvYC3lq2-cGJl7bA53o0',
                keyword=food
            )
            messages.append(TextMessage(text=dummy_response))
            print(restaurants)
            if restaurants:
                url = request.url_root.replace(
                    "http", "https") + 'static/image2.jpg'
                for i, r in enumerate(restaurants, 1):
                    print(r)
                
                columns = [
                    CarouselColumn(
                        
                        thumbnail_image_url=r['photo_url'],  # 用靜態圖
                        title=r['name'][:40],  # 限制字數
                        # 限制字數
                        text=f"{r['address'][:50]}\n⭐️{r.get('rating', 'N/A')}",
                        actions=[
                            # 必須是 https 的 URL
                            URIAction(label='查看地圖', uri=r['map_url'])
                        ]
                    )
                    for r in restaurants[:5]
                ]

                carousel_message = TemplateMessage(
                    alt_text='這是 Carousel Template',
                    template=CarouselTemplate(columns=columns)
                )
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[carousel_message]
                    )
                )
                    # messages.append(TextMessage(text='-' * 30))
            else:
                messages.append(TextMessage(text="查無相關店家"))
            Find_Restaurant = False

        if messages:
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages[:5]  # LINE 最多只允許一次回傳 5 則訊息
                )
            )


if __name__ == "__main__":
    app.run()

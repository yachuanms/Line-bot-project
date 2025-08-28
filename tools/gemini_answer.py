import random
import os
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()

#很爛的gemini 回答

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # 確保你在 .env 裡面是這樣寫的
genai.configure(api_key=GEMINI_API_KEY)

# 使用正確的模型 ID
gemini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def gemini_translate(message):
    prompt = f'幫我用指定語言翻譯以下文字，直接給我翻譯內容就好:  {message}'
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

def gemini_recommend(message):
    prompt = f'用150字告訴我 {message}'
    response = gemini_model.generate_content(prompt)
    return response.text.strip()


'''
def get_random_food():
    FOODS = ['拉麵', '牛肉麵', '壽司', '火鍋', '炒飯', '便當', '漢堡', '披薩', '義大利麵', '健康餐', '炸雞', '燒烤', '小籠包', '餃子']
    return random.choice(FOODS)

def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="line-bot")
    location = geolocator.reverse((lat, lon), language='zh-TW')
    return location.address if location else "找不到地址"

lat = 24.123552
lon = 120.675326
address = reverse_geocode(lat, lon)
print("地址：", address)

# 主程式執行
food = get_random_food()
print("隨機食物推薦：", food)
print("Gemini 餐廳推薦：", gemini_recommend("拉麵", "台北市信義區松壽路12號"))
'''
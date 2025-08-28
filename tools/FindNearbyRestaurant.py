import requests
import os
from dotenv import load_dotenv
import random
from urllib.parse import quote

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 
address = "台中市南區國光路295號"
FOODS=[]
def print_food_list():
    global FOODS
    return FOODS
def reset_food_list():
    global FOODS
    FOODS = ['拉麵', '牛肉麵', '壽司', '火鍋', '炒飯', '便當', '漢堡',
             '披薩', '義大利麵', '健康餐', '炸雞', '燒烤', '小籠包', '餃子']
# 隨機食物推薦
def get_random_food():
    global FOODS
    FOODS = ['拉麵', '牛肉麵', '壽司', '火鍋', '炒飯', '便當', '漢堡',
             '披薩', '義大利麵', '健康餐', '炸雞', '燒烤', '小籠包', '餃子']
    return random.choice(FOODS)
def clear_food():
    global FOODS
    FOODS = []
def get_food():
    global FOODS
    return random.choice(FOODS)
def insert_food(food):
    global FOODS
    FOODS.append(food)
def delete_food(food):
    global FOODS
    if food in FOODS:
        FOODS.remove(food)
# 隨機甜點推薦
def get_random_dessert():
    DESSERT = ['冰淇淋', '蛋糕', '泡芙', '布丁', '甜甜圈', '馬卡龍', '珍珠奶茶','豆花' , '仙草', '鬆餅']
    return random.choice(DESSERT)

def address_to_latlng(address, api_key):
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }
    response = requests.get(geocode_url, params=params)
    result = response.json()
    
    if result["status"] == "OK":
        location = result["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        raise Exception("Geocoding failed: " + result["status"])


def find_nearby_restaurants(latitude, longitude, radius=1000, API_KEY=GOOGLE_API_KEY, keyword="餐廳"):
    """根據經緯度與關鍵字搜尋附近餐廳，回傳名稱、地址、評分、地圖連結"""

    # Nearby Search API URL
    places_url = (
        f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'
        f'location={latitude},{longitude}&radius={radius}&type=restaurant'
        f'&keyword={keyword}&language=zh-TW&key={API_KEY}'
    )

    response = requests.get(places_url)
    result = response.json()

    restaurants = []
    if result['status'] == 'OK':
        for place in result['results']:
            name = place.get('name')
            address = place.get('vicinity')
            rating = place.get('rating')
            place_id = place.get('place_id')

            # 只保留評價大於等於 4.0 的餐廳
            if rating < 4.0:
                continue    

            details_url = (
                f"https://maps.googleapis.com/maps/api/place/details/json?"
                f"place_id={place_id}&fields=opening_hours&language=zh-TW&key={API_KEY}"
            )
            details_resp = requests.get(details_url).json()
            opening_info = details_resp.get("result", {}).get("opening_hours", {})

            # 檢查是否營業中
            if not opening_info.get("open_now", True):
                continue

            # 地圖網址格式
            map_url = f"https://www.google.com/maps/search/?api=1&query={quote(name + ' ' + address)}"

            photo_url = None
            photos = place.get('photos')
            if photos:
                photo_ref = photos[0].get('photo_reference')
                if photo_ref:
                    photo_url = get_real_photo_url(photo_ref, API_KEY)

            restaurants.append({
                'name': name,
                'address': address, 
                'rating': rating,
                'map_url': map_url,
                'photo_url': photo_url
            })
    else:
        print(f"Google API 回傳錯誤：{result.get('status')}")

    restaurants.sort(key=lambda x: x['rating'], reverse=True)
    return restaurants

def get_real_photo_url(photo_reference, api_key):
    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={api_key}"
    response = requests.get(photo_url, allow_redirects=False)
    if response.status_code == 302:
        return response.headers.get("Location")
    return None


keyWord1 = "義大利麵"
keyWord2 = get_random_dessert()
lat, lng = address_to_latlng(address, GOOGLE_API_KEY)


if __name__ == '__main__':
    if lat and lng:
            results = find_nearby_restaurants(lat, lng, keyword=keyWord2)
            print("keyword: ", keyWord2)
            for i, r in enumerate(results, 1):
                print(f"{i}. {r['name']} - {r['address']} (Rating: {r.get('rating', 'N/A')})")
                print(f"🖼️ 圖片連結：{r['photo_url']}" if r['photo_url'] else "🖼️ 沒有圖片")
                print(f"👉 地圖網址：{r['map_url']}")
                print('-' * 50)
            
    else:
        print("地址轉換失敗")


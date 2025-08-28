import requests
from math import radians, sin, cos, sqrt, atan2

import os
from dotenv import load_dotenv

load_dotenv()  # 讀取 .env 檔

CWA_API_KEY = os.getenv("CWA_API_KEY")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * \
        cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def get_public_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return None


def get_geolocation(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = res.json()
        if data['status'] == 'success':
            return {'Latitude': data['lat'], 'Longitude': data['lon']}
        return None
    except:
        return None


def find_nearest_forecast_location(user_lat, user_lon):
    url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091'
    params = {'Authorization': CWA_API_KEY,
              'downloadType': 'WEB', 'format': 'JSON'}

    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        locations = data['records']['Locations'][0]['Location']
    except Exception as e:
        print(f"❌ 錯誤：無法取得預報地區清單：{e}")
        return None

    min_dist = float('inf')
    nearest_location = None

    for loc in locations:
        try:
            lat = float(loc['Latitude'])
            lon = float(loc['Longitude'])
            dist = haversine(user_lat, user_lon, lat, lon)
            if dist < min_dist:
                min_dist = dist
                nearest_location = loc['LocationName']
        except:
            continue

    return nearest_location


def get_weather_weekly_forecast(target_location_name):
    url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091'
    params = {'Authorization': CWA_API_KEY,
              'downloadType': 'WEB', 'format': 'JSON'}

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        locations_data = data['records']['Locations'][0]['Location']
    except Exception as e:
        print(f"❌ 無法取得預報資料：{e}")
        return None

    matched = None
    for loc in locations_data:
        if loc['LocationName'] == target_location_name:
            matched = loc
            break

    if not matched:
        print(f"⚠️ 找不到地區「{target_location_name}」的預報資料")
        return None

    print(f"\n📍「{target_location_name}」近期天氣預報：")

    show_elements = ['12小時降雨機率', '最高溫度', '最低溫度', '紫外線指數']
    results = {}

    for ele in matched['WeatherElement']:
        name = ele['ElementName']
        if name not in show_elements:
            continue

        for t in ele['Time']:
            start = t['StartTime'].replace("T", " ").split("+")[0]
            end = t['EndTime'].replace("T", " ").split("+")[0]
            if not t['ElementValue']:
                continue

            value_dict = t['ElementValue'][0]
            value = list(value_dict.values())[0] if value_dict else 'N/A'

            if name == '最高溫度' and '最高溫度' not in results and value != '':
                results['最高溫度'] = value
                break
            elif name == '最低溫度' and '最低溫度' not in results and value != '':
                results['最低溫度'] = value
                break
            elif name == '紫外線指數' and '紫外線指數' not in results and value != '':
                results['紫外線指數'] = value
                break
            elif name == '12小時降雨機率' and '12小時降雨機率' not in results and value != '':
                results['12小時降雨機率'] = value
                break

    max_temp = results.get('最高溫度', 'N/A')
    min_temp = results.get('最低溫度', 'N/A')
    rain_prob = results.get('12小時降雨機率', 'N/A')
    uvi = results.get('紫外線指數', 'N/A')

    # 提醒文字
    rain_msg = ""
    uvi_msg = ""

    try:
        if int(rain_prob) > 50:
            rain_msg = "降雨機率偏高，記得攜帶雨具☔"
        else:
            rain_msg = "降雨機率偏低，外出可考慮是否攜帶雨具🌤"
    except:
        pass

    try:
        uvi_val = float(uvi)
        if uvi_val <= 2:
            uvi_msg = "紫外線低，可安心外出☘"
        elif uvi_val <= 5:
            uvi_msg = "紫外線中等，建議塗防曬😎"
        elif uvi_val <= 7:
            uvi_msg = "紫外線高，請戴帽子墨鏡🧢"
        elif uvi_val <= 10:
            uvi_msg = "紫外線非常高，減少外出🧴"
        else:
            uvi_msg = "紫外線極強，避免外出🚨"
    except:
        pass

    # 輸出到畫面
    '''
    print(f"\n【最高溫度 (°C)】{max_temp}")
    print(f"\n【最低溫度 (°C)】{min_temp}")
    print(f"\n【降雨機率 (%)】{rain_prob}")
    print(f"\n【紫外線指數】{uvi}")
    '''
    if rain_msg:
        print(rain_msg)
    if uvi_msg:
        print(uvi_msg)

    # 回傳 dictionary 結果
    return {
        "location": target_location_name,
        "max_temp": max_temp,
        "min_temp": min_temp,
        "rain_prob": rain_prob,
        "rain_message": rain_msg,
        "uvi": uvi,
        "uvi_message": uvi_msg
    }



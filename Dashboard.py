#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from inky import InkyWHAT
import requests
from bs4 import BeautifulSoup
import pytz
import os

# Config
OWM_API_KEY = "37280ef95ef1dc67f31aac66f06eb900"  # Get free at openweathermap.org
LAT, LON = 52.66, -8.62  # Limerick
ICON_DIR = "/home/pi/icons/"  # 40x40 PNGs: sunny.png, cloudy.png, rain.png
IE_TZ = pytz.timezone("Europe/Dublin")

inky = InkyWHAT("black")
img = Image.new("P", (400, 300), inky.BLACK)
draw = ImageDraw.Draw(img)

# Fonts (DejaVu on Pi)
try:
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except:
    small = ImageFont.load_default()
    med = ImageFont.load_default()
    big = ImageFont.load_default()

def get_weather():
    """OpenWeatherMap 5-day forecast"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
    resp = requests.get(url).json()
    days = []
    for i in range(0, 40, 8):  # Daily avg from 3-hour slots
        slot = resp['list'][i]
        day_str = datetime.fromtimestamp(slot['dt'], tz=IE_TZ).strftime("%a")
        temp_min = min(s['main']['temp_min'] for s in resp['list'][i:i+8])
        temp_max = max(s['main']['temp_max'] for s in resp['list'][i:i+8])
        wind = round(slot['wind']['speed'] * 3.6)  # km/h
        rain = sum(s.get('rain', {}).get('3h', 0) for s in resp['list'][i:i+8])
        icon_map = {'01d':'sunny.png', '02d':'partly.png', '03d':'cloudy.png', '09d':'rain.png', '10d':'rain.png', '11d':'storm.png', '50d':'fog.png'}
        icon_file = icon_map.get(slot['weather'][0]['icon'], 'cloudy.png')
        days.append((day_str, temp_min, temp_max, wind, rain, icon_file))
    return days[:3]

def get_tides():
    """Scrape Limerick tides (next high/low times)"""
    url = "https://tides4fishing.com/ie/munster/limerick"
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(resp.text, 'lxml')
    tides = soup.find_all('td', class_='hora')
    times = [t.text.strip() for t in tides[:4]]  # Next 2 high + 2 low
    if len(times) >= 2:
        last_turn = times[0]
        next_turn = times[1]
        direction = "Incoming" if "alta" in soup.find('td', string='Alta').find_next_sibling('td').text.lower() else "Outgoing"
        return last_turn, next_turn, direction
    return "N/A", "N/A", "Unknown"

def draw_icon(draw, icon_file, x, y):
    try:
        icon = Image.open(os.path.join(ICON_DIR, icon_file)).resize((40, 40)).convert('P')
        icon.putpalette(inky.palette())
        img.paste(icon, (x, y))
    except:
        draw.rectangle((x, y, x+40, y+40), outline=inky.WHITE, width=2)  # Fallback box

# Fetch data
weather_days = get_weather()
tide_last, tide_next, tide_dir = get_tides()
now = datetime.now(IE_TZ)
update_time = now.strftime("%H:%M")

# Grid lines
draw.line((200, 20), (200, 279), fill=inky.WHITE, width=2)  # Vertical
draw.line((20, 160), (379, 160), fill=inky.WHITE, width=1)  # Horizontal

# Panel 1: Weather (top-left 20-199, 20-159)
for i, (day, tmin, tmax, wind, rain, icon) in enumerate(weather_days):
    y_base = 25 + i * 45
    draw.text((25, y_base), day, fill=inky.WHITE, font=med)
    draw_icon(draw, icon, 25, y_base + 20)
    temps = f"{int(tmin)}/{int(tmax)}"
    w, h = draw.textsize(temps, big)
    draw.text((70, y_base + 27, temps, fill=inky.WHITE, font=big))
    draw.text((25, y_base + 75), f"Wind {wind}kmh", fill=inky.WHITE, font=small)
    draw.text((25, y_base + 90), f"{rain:.0f}mm", fill=inky.WHITE, font=small)

# Panel 2: Rain (top-right 200-379, 20-159)
draw.text((240, 25), "Next 3h", fill=inky.WHITE, font=med)
draw_icon(draw, 'rain.png', 235, 45)  # Placeholder; customize with real data
rain_h = [1, 0, 3]  # Mock mm; replace with forecast['rain']
for i, mm in enumerate(rain_h):
    draw.text((240, 95 + i*20), f"{mm}mm", fill=inky.WHITE, font=med)

# Panel 3: Tide (bottom-left 20-199, 160-279)
draw_icon(draw, f"tide_{tide_dir.lower().replace(' ','')}.png' if exists else box, 25, 165)
draw.text((70, 170), f"Last: {tide_last}", fill=inky.WHITE, font=small)
draw.text((70, 190), f"Next: {tide_next}", fill=inky.WHITE, font=small)
draw.text((25, 215), tide_dir, fill=inky.WHITE, font=med)

# Panel 4: Date (bottom-right 200-379, 160-279)
date_str = now.strftime("%a %d/%m/%y")
w, h = draw.textsize(date_str, big)
draw.text((240 - w//2, 170), date_str, fill=inky.WHITE, font=big)
draw.text((240 - 40, 205), f"Last update: {update_time}", fill=inky.WHITE, font=small)

# Update display
inky.set_image(img)
inky.show()
print(f"Dashboard updated at {update_time}")

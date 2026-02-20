#!/usr/bin/env python3
"""
Complete Inky wHAT Dashboard - Limerick Weather & Tide
All syntax errors fixed: draw.text(), f-strings, palette, icons
Ronan - Feb 2026
"""

import sys
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from inky import InkyWHAT
import requests
from bs4 import BeautifulSoup
import pytz

# === CONFIG ===
OWM_API_KEY = "YOUR_API_KEY_HERE"  # https://openweathermap.org
LAT, LON = 52.66, -8.62  # Limerick
ICON_DIR = "./icons/"  # 40x40 PNGs: sunny.png cloudy.png rain.png tide_incoming.png tide_outgoing.png
IE_TZ = pytz.timezone("Europe/Dublin")

# Init display & image
inky = InkyWHAT("black")  # Fast B/W mode
img = Image.new("P", (400, 300), 0)  # Black background

# Set explicit B/W palette (index 0=black, 255=white)
palette = [0]*768  # 256*3 bytes
palette[0:3] = [0,0,0]    # Index 0: Black
palette[765:768] = [255,255,255]  # Index 255: White
img.putpalette(palette)

draw = ImageDraw.Draw(img)

# Load fonts (fallback to default if missing)
try:
    font_dir = "/usr/share/fonts/truetype/dejavu/"
    small = ImageFont.truetype(font_dir + "DejaVuSans-Bold.ttf", 14)
    med = ImageFont.truetype(font_dir + "DejaVuSans-Bold.ttf", 20)
    big = ImageFont.truetype(font_dir + "DejaVuSans-Bold.ttf", 24)
except:
    small = ImageFont.load_default()
    med = ImageFont.load_default()
    big = ImageFont.load_default()

def draw_icon(draw, icon_file, x, y):
    """Draw 40x40 icon or white X fallback"""
    icon_path = os.path.join(ICON_DIR, icon_file)
    try:
        icon = Image.open(icon_path).resize((40, 40)).convert('P')
        icon.putpalette(palette)
        img.paste(icon, (x, y))
    except:
        # White X fallback
        draw.rectangle((x, y, x+40, y+40), fill=0, outline=255, width=2)
        draw.line((x+5, y+5), (x+35, y+35), fill=255, width=3)
        draw.line((x+35, y+5), (x+5, y+35), fill=255, width=3)
        print(f"Missing icon: {icon_path}")

def get_weather():
    """OpenWeatherMap forecast - Limerick"""
    if OWM_API_KEY == "YOUR_API_KEY_HERE":
        return [("Mon", 12, 18, 15, 2, "cloudy.png"),
                ("Tue", 10, 16, 12, 0, "sunny.png"),
                ("Wed", 11, 17, 18, 5, "rain.png")]  # Mock data
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric"
        resp = requests.get(url, timeout=10).json()
        days = []
        icon_map = {'01d':'sunny.png', '02d':'partly.png', '03d':'cloudy.png', 
                   '09d':'rain.png', '10d':'rain.png', '11d':'storm.png', '50d':'fog.png'}
        
        for i in range(0, 24, 8):  # 3 days
            if i >= len(resp['list']): break
            slot = resp['list'][i]
            day_str = datetime.fromtimestamp(slot['dt'], tz=IE_TZ).strftime("%a")
            temps = [s['main'] for s in resp['list'][i:i+8]]
            tmin = min(t['temp_min'] for t in temps)
            tmax = max(t['temp_max'] for t in temps)
            wind = round(slot['wind']['speed'] * 3.6)  # km/h
            rain = sum(s.get('rain', {}).get('3h', 0) for s in resp['list'][i:i+8])
            icon = icon_map.get(slot['weather'][0]['icon'], 'cloudy.png')
            days.append((day_str, tmin, tmax, wind, rain, icon))
        return days
    except Exception as e:
        print(f"Weather error: {e}")
        return [("Err", 0, 0, 0, 0, "cloudy.png")] * 3

def get_tides():
    """Scrape Limerick Dock tides"""
    try:
        url = "https://tides4fishing.com/ie/munster/limerick"
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; PiDashboard/1.0)'}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'lxml')
        tide_times = soup.find_all('td', class_='hora')[:4]
        times = [t.text.strip() for t in tide_times]
        
        if len(times) >= 2:
            last_turn = times[0]
            next_turn = times[1]
            # Simple direction from table context
            direction = "Incoming" if len(times) > 2 and "alta" in str(soup).lower() else "Outgoing"
            return last_turn, next_turn, direction
        
        return "N/A", "N/A", "Unknown"
    except Exception as e:
        print(f"Tide error: {e}")
        return "N/A", "N/A", "Error"

# === FETCH DATA ===
print("Fetching data...")
weather_days = get_weather()
tide_last, tide_next, tide_dir = get_tides()
now = datetime.now(IE_TZ)
update_time = now.strftime("%H:%M")

print(f"Weather: {len(weather_days)} days | Tides: {tide_dir}")

# === DRAW GRID ===
draw.line((200, 20), (200, 279), fill=255, width=2)  # Vertical split
draw.line((20, 160), (379, 160), fill=255, width=1)  # Horizontal split

# === PANEL 1: WEATHER (Top-left 180x140) ===
for i, (day, tmin, tmax, wind, rain, icon) in enumerate(weather_days):
    y_base = 25 + i * 45
    draw.text((25, y_base), day, fill=255, font=med)
    draw_icon(draw, icon, 25, y_base + 20)
    temps = f"{int(tmin)}/{int(tmax)}"
    draw.text((70, y_base + 27), temps, fill=255, font=big)
    draw.text((25, y_base + 75), f"W{wind}", fill=255, font=small)
    draw.text((80, y_base + 75), f"R{rain:.0f}", fill=255, font=small)

# === PANEL 2: RAIN (Top-right 180x140) ===
draw.text((240, 25), "Rain 3h", fill=255, font=med)
draw_icon(draw, "rain.png", 235, 45)
# Mock hourly - replace with real OWM hourly data
rain_h = [1.2, 0.0, 3.5]
for i, mm in enumerate(rain_h):
    draw.text((240, 95 + i*20), f"{mm}mm", fill=255, font=med)

# === PANEL 3: TIDE (Bottom-left 180x120) ===
if tide_dir == "Incoming":
    tide_icon = "tide_incoming.png"
elif tide_dir == "Outgoing":
    tide_icon = "tide_outgoing.png"
else:
    tide_icon = "unknown.png"
draw_icon(draw, tide_icon, 25, 165)

draw.text((70, 170), f"Last: {tide_last}", fill=255, font=small)
draw.text((70, 190), f"Next: {tide_next}", fill=255, font=small)
draw.text((25, 215), tide_dir[:8], fill=255, font=med)  # Truncate if long

# === PANEL 4: DATE (Bottom-right 180x120) ===
date_str = now.strftime("%a %d/%m/%y")
w, _ = draw.textsize(date_str, font=big)
draw.text((240 - w//2, 170), date_str, fill=255, font=big)
draw.text((240 - 40, 205), f"Updated: {update_time}", fill=255, font=small)

# === DISPLAY ===
print("Drawing complete...")
inky.set_image(img)
inky.show()
print("Dashboard updated successfully!")

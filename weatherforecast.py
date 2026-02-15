import requests
from datetime import datetime, timedelta, timezone


API_KEY = "7d06afb4-0863-11f1-ae7c-0242ac120004-7d06b00e-0863-11f1-ae7c-0242ac120004"

# Kilkee, Co. Clare approximate coordinates
LAT = 52.681
LON = -9.648

## Limerick coordinates
##LAT = 52.6638
##LON = -8.6267

def get_kilkee_tides(hours_ahead=48):
    # Stormglass uses ISO8601 times in UTC
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=hours_ahead)

    params = {
        "lat": LAT,
        "lng": LON,
        "start": int(now.timestamp()),
        "end": int(end.timestamp())
    }

    headers = {
        "Authorization": API_KEY
    }

    url = "https://api.stormglass.io/v2/tide/extremes/point"

    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # Each entry has 'type' ('high'/'low') and 'time' plus 'height'
    tides = []
    for t in data.get("data", []):
        tide_time = datetime.fromisoformat(t["time"].replace("Z", "+00:00"))
        tides.append({
            "time_utc": tide_time,
            "type": t["type"],
            "height_m": t.get("height")
        })

    return tides

def get_weather_forecast():
    """
    Get rainfall for next 3 hours and weather forecast for next 3 days
    """
    
    # API endpoint
    url = "https://api.open-meteo.com/v1/forecast"
    
    # Parameters for the API request
    params = {
        'latitude': LAT,
        'longitude': LON,
        'hourly': 'precipitation,temperature_2m,weather_code,wind_speed_10m',
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max',
        'timezone': 'Europe/Dublin',
        'forecast_days': 3
    }
    
    # Make the API request
    response = requests.get(url, params=params)
    data = response.json()
    
    # Extract hourly data for next 3 hours
    print("=" * 60)
    print("RAINFALL FORECAST - NEXT 3 HOURS")
    print("=" * 60)
    
    hourly_data = data['hourly']
    current_time = datetime.now()
    
    for i in range(3):
        time_str = hourly_data['time'][i]
        precipitation = hourly_data['precipitation'][i]
        temp = hourly_data['temperature_2m'][i]
        wind = hourly_data['wind_speed_10m'][i]
        
        print(f"\nHour {i+1}: {time_str}")
        print(f"  Rainfall: {precipitation} mm")
        print(f"  Temperature: {temp}°C")
        print(f"  Wind Speed: {wind} km/h")
    
    # Extract daily forecast for next 3 days
    print("\n" + "=" * 60)
    print("3-DAY WEATHER FORECAST")
    print("=" * 60)
    
    daily_data = data['daily']
    
    for i in range(3):
        date_str = daily_data['time'][i]
        temp_max = daily_data['temperature_2m_max'][i]
        temp_min = daily_data['temperature_2m_min'][i]
        precip_sum = daily_data['precipitation_sum'][i]
        wind_max = daily_data['wind_speed_10m_max'][i]
        weather_code = daily_data['weather_code'][i]
        
        # Weather code interpretation
        weather_desc = interpret_weather_code(weather_code)
        
        print(f"\n{date_str} ({get_day_name(date_str)})")
        print(f"  Conditions: {weather_desc}")
        print(f"  Temperature: {temp_min}°C - {temp_max}°C")
        print(f"  Total Rainfall: {precip_sum} mm")
        print(f"  Max Wind Speed: {wind_max} km/h")
    
    return data

def interpret_weather_code(code):
    """
    Interpret WMO weather codes
    """
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(code, f"Unknown (code: {code})")

def get_day_name(date_str):
    """
    Convert date string to day name
    """
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.strftime('%A')

# Run the forecast
if __name__ == "__main__":
    weather_data = get_weather_forecast()
    tides = get_kilkee_tides()

    message = "Upcoming tides for Kilkee (UTC):"
    print(message)

    for t in tides:
        message = f"{t['time_utc']}  {t['type']:4}  {t['height_m']:.2f} m"
        print(message)



#!/usr/bin/env python3
"""\
weather.py 2023 Nulluminati (https://github.com/Nulluminati)

Gets the weather, atmospheric conditions, and icon from openweathermap.
Intended for use in polybar.
Icons are from Nerd Font.

Usage: weather.py
"""

import requests
import os

# Openweather API Key
api_key = os.environ.get('OPENWEATHER_API_KEY', '')

if not api_key:
    print("")
    exit(1)

# City/Town
location = "Vancouver"

# standard, imperial or metric
units = "metric"

# Weather icon codes from https://openweathermap.org/weather-conditions
weather_icons = {
    "01d": "", # Clear sky day
    "01n": "󰖔", # Clear sky night
    "02d": "", # Few clouds day
    "02n": "", # Few clouds night
    "03d": "", # Scattered clouds day
    "03n": "", # Scattered clouds night
    "04d": "", # Broken clouds day
    "04n": "", # Broken clouds night
    "09d": "", # Shower rain day
    "09n": "", # Shower rain night
    "10d": "", # Rain day
    "10n": "", # Rain night
    "11d": "", # Thunderstorm day
    "11n": "", # Thunderstorm night
    "13d": "", # Snow day
    "13n": "", # Snow night
    "50d": "", # Mist day
    "50n": "", # Mist night
}

# Get the weather data from the OpenWeatherMap API
try:
    weather_request = requests.get("http://api.openweathermap.org/data/2.5/weather?q=" + location + "&appid=" + api_key + "&units=" + units )
    weather_data = weather_request.json()
except:
    print("")
    exit(1)

if weather_request.status_code != 200:
    print("")
    exit(1)

# Get the temperature
temp = weather_data["main"]["temp"]

# Get the weather icon
icon = weather_data["weather"][0]["icon"]

# Get the icon from the dictionary
try:
    icon = weather_icons[icon]
except:
    icon = ""

# Print the weather info
print(str(round(temp)) + "° " + icon)

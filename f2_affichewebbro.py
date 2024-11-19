import requests
import folium
from pymongo import MongoClient

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['veli_db']
collection = db['velib_t_reel']

# Create a Folium map centered around Paris
map_paris = folium.Map(location=[48.84, 2.26], zoom_start=12)

# Fetch Velib station data
velib_api_url = 'https://api.jcdecaux.com/vls/v1/stations?contract=Paris&apiKey=YOUR_API_KEY'
response = requests.get(velib_api_url)
stations = response.json()

# Add markers for Velib stations
for station in stations:
    folium.Marker(
        location=[station['position']['lat'], station['position']['lng']],
        popup=station['name'],
        icon=folium.Icon(color='blue')  # Customize the icon as needed
    ).add_to(map_paris)

# Add existing MongoDB entries to the map (if applicable)
for entry in collection.find():
    folium.Marker(
        location=[entry['latitude'], entry['longitude']],
        popup=entry['name'],
        icon=folium.Icon(color='green')
    ).add_to(map_paris)

# Save the map to an HTML file
map_paris.save('paris_map.html')

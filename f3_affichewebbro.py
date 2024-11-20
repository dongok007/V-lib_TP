from flask import Flask, request
import folium
from pymongo import MongoClient
from geopy.geocoders import Nominatim
from geopy.distance import great_circle

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['veli_db']
collection = db['velib_t_reel']

@app.route('/')
def home():
    return """
    <h1>Bienvenue sur l'application Velib</h1>
    <p>Veuillez fournir une adresse à <a href="/map?address=Châtelet, Paris">/map</a> pour voir les stations Velib proches.</p>
    """

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/map')
def map():
    address = request.args.get('address')
    if not address:
        return "Adresse non fournie.", 400

    geolocator = Nominatim(user_agent="velib_locator")
    location = geolocator.geocode(address)
    if not location:
        return "Adresse non trouvée.", 404

    address_coordinates = (location.latitude, location.longitude)
    map_address = folium.Map(location=address_coordinates, zoom_start=15)
    folium.Marker(
        location=address_coordinates,
        popup=f"Adresse: {address}",
        icon=folium.Icon(color='red')
    ).add_to(map_address)

    stations = collection.find()
    nearby_stations = []

    for station in stations:
        try:
            name = station['name']
            lat = station['coordonnees_geo']['lat']
            lon = station['coordonnees_geo']['lon']
            num_bikes = station['numBikesAvailable']
            station_coordinates = (lat, lon)
            distance = great_circle(address_coordinates, station_coordinates).meters
            if distance <= 500:
                nearby_stations.append((name, lat, lon, num_bikes, distance))
                folium.Marker(
                    location=station_coordinates,
                    popup=f"Station: {name}<br>Vélos disponibles: {num_bikes}<br>Distance: {distance:.2f} m",
                    icon=folium.Icon(color='green')
                ).add_to(map_address)
        except KeyError as e:
            print(f"Erreur dans les données de station : {e}")

    map_html = map_address._repr_html_()
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Carte des Stations Velib</title>
    </head>
    <body>
        <h1>Carte des Stations Velib proches de : {address}</h1>
        <div>{map_html}</div>
        <h2>Stations proches :</h2>
        <ul>
            {"".join([f"<li>{name} - {distance:.2f} m, vélos disponibles : {num_bikes}</li>" for name, lat, lon, num_bikes, distance in nearby_stations])}
        </ul>
    </body>
    </html>
    """
    return html_content

if __name__ == '__main__':
    app.run(debug=True)

import webbrowser
import folium
import pymongo
import requests  # Import requests for API calls


# Function to connect to MongoDB
def connect_to_mongodb(db_name, collection_name):
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")  # Connect to MongoDB server
        db = client['velib_db']  # Use the provided database name
        collection = db['stations']  # Use the provided collection name
        print("Connexion à MongoDB réussie.")
        return collection
    except Exception as e:
        print(f"Erreur lors de la connexion à MongoDB : {e}")
        return None


# Function to fetch data from an API
def fetch_data_from_api(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données de l'API : {e}")
        return None


# Function to insert data into MongoDB
def insert_data_into_mongodb(collection, data):
    if data:
        try:
            # Assume data is a list of dictionaries (documents)
            result = collection.insert_many(data)
            print(f"{len(result.inserted_ids)} documents insérés avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'insertion dans MongoDB : {e}")
    else:
        print("Aucune donnée à insérer.")


# Connect to the MongoDB
mycol = connect_to_mongodb("veli_db", "stations")  # Connect to the specified database and collection

# Fetch data from the API
api_url = 'https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?limit=20'
data_from_api = fetch_data_from_api(api_url)

# Print the raw data fetched from the API
print("Raw data fetched from API:", data_from_api)  # Print the entire API response for debugging

if data_from_api:
    # Check if 'records' exists and is a list
    if 'records' in data_from_api and isinstance(data_from_api['records'], list):
        records = data_from_api['records']

        # Process records to match MongoDB document structure
        processed_records = []
        for record in records:
            fields = record.get('fields', {})
            geo = fields.get('geolocalisation', {})
            processed_records.append({
                'name': fields.get('name', 'Unknown Place'),
                'lat': geo.get('lat'),
                'lng': geo.get('lng')
            })

        # Remove any records that don't have lat/lng
        processed_records = [r for r in processed_records if r['lat'] is not None and r['lng'] is not None]

        # Insert fetched and processed records into MongoDB
        insert_data_into_mongodb(mycol, processed_records)
    else:
        print("The 'records' key is missing or is not a list in the API response.")
else:
    print("No data was returned from the API.")

# Retrieve entries from MongoDB
if mycol is not None:  # Check if the collection is valid
    entries = list(mycol.find())

    # Create the map
    m = folium.Map(location=[48.821270, 2.311693], tiles="OpenStreetMap", zoom_start=15)

    # Add markers to the map
    for i, item in enumerate(entries):
        if i < 100:  # Limit to 100 markers
            lat = item.get('lat')  # Get latitude directly
            lng = item.get('lng')  # Get longitude directly
            name = item.get('name', 'Unknown Place')  # Get name directly

            if lat and lng:
                folium.Marker(
                    [lat, lng],
                    popup=f"<i>{name}</i>",
                    tooltip=f'<b>{name}</b>'
                ).add_to(m)

    # Save the HTML file and open it in a web browser
    m.save("map.html")
    webbrowser.open('map.html')

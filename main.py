import requests
#agricultura familiar de subsistência, selo organico, tecnologia de irrigação, sistemas de irrigação componentes básicos, abordagem da captação de sinais via satélite por infravermelho, podemos usar chatGPT. dados de elevação para apoiar a decisão dos carneiros
API_KEY = 'AIzaSyCHfKgESVCt6zp5IdmfOYHxs1ljjLUYLsA'
BASE_URL = 'https://maps.googleapis.com/maps/api/elevation/json'


def get_elevation(lat, lng):
    params = {
        'locations': f"{lat},{lng}",
        'key': API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if data.get('results'):
        elevation = data['results'][0]['elevation']
        return elevation
    else:
        return None


latitude = -23.470049
longitude = -47.429751

elevation = get_elevation(latitude, longitude)

if elevation is not None:
    print(f"Elevation at ({latitude}, {longitude}): {elevation} meters")
else:
    print("Elevation data not available")

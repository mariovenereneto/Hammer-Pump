import requests

def extract_value(lat, long, area):
    # Define the URL with the provided parameters
    url = f'http://www.leb.esalq.usp.br/wolff/rv/resultado.php?lat={lat}&long={long}&area={area}'

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Split the HTML content by lines
        lines = response.text.split('\n')

        # Iterate through the lines to find the row with "Q7,10"
        for line in lines:
            if '7,10' in line:
                # Split the line by "</td>" to extract the values
                values = line.split('</td>')

                # The value you want is the last part of the line
                target_value = values[-2].split('>')[-1].strip()

                return target_value  # Return the extracted value
        else:
            return "Row with 'Q7,10' not found in the HTML content"
    else:
        return "Failed to retrieve the web page"

# Example usage of the function:
lat = '-23.47'
long = '-47.4297'
area = '10'
result = extract_value(lat, long, area)
print(f"The extracted value is: {result}")

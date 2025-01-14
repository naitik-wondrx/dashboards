from geopy.geocoders import Nominatim
import pandas as pd
import time

# Load the data
file_path = 'lupin-digitization.xlsx'
data = pd.read_excel(file_path, sheet_name='Result 1')

# Extract unique cities from the dataset
cities = data['state_name'].unique()

# Initialize geolocator
geolocator = Nominatim(user_agent="naitik370@gmail.com")

# Function to get coordinates
def get_coordinates(row):
        # Properly access city and state from the row
    city_name = row['state']
    
    # Pass city and state in the geocode query
    location = geolocator.geocode(f"{city_name}, India")
    
    if location:
        return pd.Series([location.latitude, location.longitude])
    else:
        return pd.Series([None, None])
city_coords = pd.DataFrame(cities, columns=['state'])
city_coords[['latitude', 'longitude']] = city_coords.apply(get_coordinates, axis=1)

# Save the coordinates to avoid repeated API calls
city_coords.to_csv('state_coordinates.csv', index=False)

print(city_coords)

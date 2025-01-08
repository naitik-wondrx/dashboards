import pandas as pd

# Load data and state coordinates
def load_data(file_path, sheet_name, state_coord_path):
    data = pd.read_excel(file_path, sheet_name=sheet_name)
    state_coords = pd.read_csv(state_coord_path)
    return data, state_coords

# Medical term mapping for standardization
medical_terms = {
    "COMPLETE BLOOD COUNT; CBC": "CBC",
    "B12": "Vitamin B12",
    "D3": "Vitamin D3",
    "BP": "Blood Pressure",
    "UTI": "Urinary Tract Infection",
    "Hb": "Hemoglobin",
    "ECG": "Electrocardiogram",
    "MRI": "Magnetic Resonance Imaging",
}

# Preprocessing function
def preprocess_data(data):
    # Standardize medical terms
    data['type'] = data['type'].replace(medical_terms)
    data['value'] = data['value'].replace(medical_terms)

    # Handle age group bins
    age_bins = [0, 18, 30, 40, 50, 60, 70, 100]
    age_labels = ['<18', '18-30', '30-40', '40-50', '50-60', '60-70', '70+']
    data['age_group'] = pd.cut(data['age'], bins=age_bins, labels=age_labels)

    # Gender normalization (e.g., standardize M/F inputs)
    data['gender'] = data['gender'].replace({'M': 'Male', 'F': 'Female'})

    # Fill missing or incorrect state/city names if necessary
    data['state_name'] = data['state_name'].str.title()
    data['city'] = data['city'].str.title()

    return data

# Function to save preprocessed data
def save_preprocessed_data(data, save_path='preprocessed_data.csv'):
    data.to_csv(save_path, index=False)
    print(f"Data saved to {save_path}")

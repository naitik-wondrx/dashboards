import streamlit as st
import pandas as pd
import plotly.express as px

# Load the data
file_path = 'Gynaecology-Digitized-dataset.xlsx'
data = pd.read_excel(file_path, sheet_name='result 1')
# Load the CSV with state coordinates
state_coords = pd.read_csv('state_coordinates.csv')

# Sidebar filters
st.sidebar.title("Filters")
state_filter = st.sidebar.multiselect("Select State", data['state_name'].unique())
city_filter = st.sidebar.multiselect("Select City", data['city'].unique())

# Filter data based on user input
filtered_data = data.copy()
if state_filter:
    filtered_data = filtered_data[filtered_data['state_name'].isin(state_filter)]
if city_filter:
    filtered_data = filtered_data[filtered_data['city'].isin(city_filter)]

filtered_data = filtered_data.applymap(lambda x: x.strip() if isinstance(x, str) else x)

filtered_data['value'] = filtered_data['value'].apply(lambda x: 'ABDOMEN' if 'ABD' in str(x).lower() else x)



filtered_data['value'] = filtered_data['value'].apply(lambda x: 'CBC' if 'cbc' in str(x).lower() else x)
filtered_data['value'] = filtered_data['value'].apply(lambda x: 'URINE' if 'urine' in str(x).lower() else x)
filtered_data['value'] = filtered_data['value'].apply(lambda x: 'HBSAG' if 'hbsag' in str(x).lower() else x)
# Title
st.title("Gynaecology Patient Data Dashboard")

# Aggregate by state
state_counts = filtered_data.groupby('state_name').size().reset_index(name='count')

# Merge state data with coordinates
merged_state_data = pd.merge(state_counts, state_coords, on='state_name', how='left')
merged_state_data = merged_state_data.dropna(subset=['latitude', 'longitude'])  # Drop rows with missing coordinates

# Aggregate by city
city_counts = filtered_data.groupby('city').size().reset_index(name='count')
city_counts = city_counts.sort_values(by='count', ascending=True)

# Tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📍 City & State Distribution",
    "📊 Demographics",
    "🩺 Observations & Diagnostics",
    "💊 Medicines",
    "🏭 Pharma Analytics"
])

# --------------------
# 1. City & State Distribution
# --------------------
with tab1:
    st.title("State-wise and City-wise Patient Distribution")

    # --- State-wise Distribution ---
    st.subheader("🌐 State-wise Patient Distribution on Map")
    state_data = merged_state_data[['state_name', 'count']].sort_values(by='count', ascending=False).reset_index(drop=True)
    st.dataframe(state_data)

    fig_state = px.scatter_mapbox(
        merged_state_data,
        lat='latitude',
        lon='longitude',
        size='count',
        hover_name='state_name',
        zoom=4,
        mapbox_style="carto-positron",
        title="Patient Distribution by State"
    )

    fig_state.update_layout(
        mapbox=dict(
            center=dict(lat=20.5937, lon=78.9629),  # Centered on India
            zoom=4
        )
    )
    st.plotly_chart(fig_state)

    # --- City-wise Distribution ---
    st.subheader("🏙️ City-wise Patient Distribution (Bar Chart)")

    fig_city = px.bar(
        city_counts,
        x='count',
        y='city',
        orientation='h',
        title="Patient Distribution by City"
    )
    st.plotly_chart(fig_city)
    st.dataframe(city_counts)

# --------------------
# 2. Demographic Analysis
# --------------------
with tab2:
    st.subheader("📊 Demographic Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Age Group Distribution")
        age_bins = [0, 18, 30, 40, 50, 60, 70, 100]
        age_labels = ['<18', '18-30', '30-40', '40-50', '50-60', '60-70', '70+']
        filtered_data['age_group'] = pd.cut(filtered_data['age'], bins=age_bins, labels=age_labels)
        age_group_counts = filtered_data['age_group'].value_counts().reset_index()
        age_group_counts.columns = ['age_group', 'count']
        age_group_counts = age_group_counts.sort_values(by='count', ascending=True)
        st.bar_chart(age_group_counts.set_index('age_group'))

    with col2:
        st.write("### Gender Distribution")
        gender_counts = filtered_data['gender'].value_counts().reset_index()
        gender_counts.columns = ['gender', 'count']
        gender_counts = gender_counts.sort_values(by='count', ascending=True)
        st.bar_chart(gender_counts.set_index('gender'))

# --------------------
# 3. Observations & Diagnostics
# --------------------
with tab3:
    st.subheader("🩺 Top Observations")

    top_10_observations = (
        filtered_data[filtered_data['type'] == 'Observation']['value']
        .value_counts()
        .nlargest(10)
        .reset_index()
    )
    top_10_observations.columns = ['Observation', 'Count']
    top_10_observations = top_10_observations.sort_values(by='Count', ascending=True)

    st.plotly_chart(px.bar(top_10_observations, y='Observation', x='Count', orientation='h'))
    st.table(top_10_observations)

    # Replace 'COMPLETE BLOOD COUNT; CBC' with 'CBC' in 'type' column

    st.subheader("🧬 Top 10 Diagnostics")
    top_10_diagnostics = (
        filtered_data[filtered_data['type'] == 'Diagnostic']['value']
        .value_counts()
        .nlargest(20)
        .reset_index()
    )
    top_10_diagnostics.columns = ['Diagnostic', 'Count']
    st.plotly_chart(px.bar(top_10_diagnostics, y='Diagnostic', x='Count', orientation='h'))
    st.table(top_10_diagnostics)

# --------------------
# 4. Medicines
# --------------------
with tab4:
    st.subheader("💊 Top 10 Medicines")

    top_10_medicines = (
        filtered_data[filtered_data['type'] == 'Medicine']['value']
        .value_counts()
        .nlargest(10)
        .reset_index()
    )
    top_10_medicines.columns = ['Medicine', 'Count']
    st.plotly_chart(px.bar(top_10_medicines, y='Medicine', x='Count', orientation='h'))
    st.table(top_10_medicines)

# --------------------
# 5. Pharma Analytics
# --------------------
with tab5:
    st.subheader("🏭 Top 17 Medicine Manufacturers")
    top_17_manufacturers = (
        filtered_data['manufacturers']
        .value_counts()
        .nlargest(17)
        .reset_index()
    )
    top_17_manufacturers.columns = ['Manufacturers', 'Count']
    st.plotly_chart(px.bar(top_17_manufacturers, y='Manufacturers', x='Count', orientation='h'))

    st.subheader("🔍 Top 15 Medications Primary Use")
    top_15_primary_use = (
        filtered_data['primary_use']
        .value_counts()
        .nlargest(15)
        .reset_index()
    )
    top_15_primary_use.columns = ['Primary Use', 'Count']
    st.plotly_chart(px.bar(top_15_primary_use, y='Primary Use', x='Count', orientation='h'))

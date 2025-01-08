import streamlit as st
import pandas as pd
import plotly.express as px

def load_data(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)

def load_state_coords(file_path):
    return pd.read_csv(file_path)

def apply_filters(data, state_filter, city_filter):
    filtered_data = data.copy()
    if state_filter:
        filtered_data = filtered_data[filtered_data['state_name'].isin(state_filter)]
    if city_filter:
        filtered_data = filtered_data[filtered_data['city'].isin(city_filter)]
    return filtered_data

def clean_data(data):
    data = data.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    data['value'] = data['value'].apply(lambda x: ' '.join([word if word.lower() != 'abd' else 'abdomen' for word in str(x).split()]))
    data['value'] = data['value'].apply(lambda x: 'CBC' if 'cbc' in str(x).lower() else x)
    data['value'] = data['value'].apply(lambda x: 'URINE' if 'urine' in str(x).lower() else x)
    data['value'] = data['value'].apply(lambda x: 'HBSAG' if 'hbsag' in str(x).lower() else x)
    return data

def aggregate_data(data):
    state_counts = data.groupby('state_name').size().reset_index(name='count')
    city_counts = data.groupby('city').size().reset_index(name='count').sort_values(by='count', ascending=True)
    return state_counts, city_counts

def merge_state_data(state_counts, state_coords):
    merged_state_data = pd.merge(state_counts, state_coords, on='state_name', how='left')
    return merged_state_data.dropna(subset=['latitude', 'longitude'])

def plot_state_distribution(merged_state_data):
    fig_state = px.scatter_mapbox(
        merged_state_data,
        lat='latitude',
        lon='longitude',
        size='count',
        hover_name='state_name',
        zoom=3,
        mapbox_style="dark",
        title="Patient Distribution by State"
    )
    fig_state.update_layout(
        mapbox=dict(
            center=dict(lat=20.5937, lon=78.9629),  # Centered on India
            zoom=3
        )
    )
    return fig_state

def plot_city_distribution(city_counts):
    fig_city = px.bar(
        city_counts,
        x='count',
        y='city',
        orientation='h',
        title="Patient Distribution by City"
    )
    return fig_city

def plot_demographics(filtered_data):
    age_bins = [0, 18, 30, 40, 50, 60, 70, 100]
    age_labels = ['<18', '18-30', '30-40', '40-50', '50-60', '60-70', '70+']
    filtered_data['age_group'] = pd.cut(filtered_data['age'], bins=age_bins, labels=age_labels)
    age_group_counts = filtered_data['age_group'].value_counts().reset_index()
    age_group_counts.columns = ['age_group', 'count']
    age_group_counts = age_group_counts.sort_values(by='count', ascending=True)

    gender_counts = filtered_data['gender'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']
    gender_counts = gender_counts.sort_values(by='count', ascending=True)

    return age_group_counts, gender_counts

def plot_observations(filtered_data):
    top_10_observations = (
        filtered_data[filtered_data['type'] == 'Observation']['value']
        .value_counts()
        .nlargest(10)
        .reset_index()
    )
    top_10_observations.columns = ['Observation', 'Count']
    top_10_observations = top_10_observations.sort_values(by='Count', ascending=True)

    top_10_diagnostics = (
        filtered_data[filtered_data['type'] == 'Diagnostic']['value']
        .value_counts()
        .nlargest(20)
        .reset_index()
    )
    top_10_diagnostics.columns = ['Diagnostic', 'Count']

    return top_10_observations, top_10_diagnostics

def plot_medicines(filtered_data):
    top_10_medicines = (
        filtered_data[filtered_data['type'] == 'Medicine']['value']
        .value_counts()
        .nlargest(10)
        .reset_index()
    )
    top_10_medicines.columns = ['Medicine', 'Count']
    return top_10_medicines

def plot_pharma_analytics(filtered_data):
    top_17_manufacturers = (
        filtered_data['manufacturers']
        .value_counts()
        .nlargest(17)
        .reset_index()
    )
    top_17_manufacturers.columns = ['Manufacturers', 'Count']

    top_15_primary_use = (
        filtered_data['primary_use']
        .value_counts()
        .nlargest(15)
        .reset_index()
    )
    top_15_primary_use.columns = ['Primary Use', 'Count']

    return top_17_manufacturers, top_15_primary_use

def main():
    # Load the data
    file_path = 'Gynaecology-Digitized-dataset.xlsx'
    data = load_data(file_path, sheet_name='result 1')
    state_coords = load_state_coords('state_coordinates.csv')

    # Sidebar filters
    st.sidebar.title("Filters")
    state_filter = st.sidebar.multiselect("Select State", data['state_name'].unique())
    city_filter = st.sidebar.multiselect("Select City", data['city'].unique())

    # Filter and clean data
    filtered_data = apply_filters(data, state_filter, city_filter)
    filtered_data = clean_data(filtered_data)

    # Aggregate data
    state_counts, city_counts = aggregate_data(filtered_data)
    merged_state_data = merge_state_data(state_counts, state_coords)

    # Title
    st.title("Gynaecology Patient Data Dashboard")

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📍 City & State Distribution",
        "📊 Demographics",
        "🩺 Observations & Diagnostics",
        "💊 Medicines",
        "🏭 Pharma Analytics"
    ])

    # 1. City & State Distribution
    with tab1:
        st.title("State-wise and City-wise Patient Distribution")
        st.subheader("🌐 State-wise Patient Distribution on Map")
        st.dataframe(merged_state_data[['state_name', 'count']].sort_values(by='count', ascending=False).reset_index(drop=True))
        st.plotly_chart(plot_state_distribution(merged_state_data))
        st.subheader("🏙️ City-wise Patient Distribution (Bar Chart)")
        st.plotly_chart(plot_city_distribution(city_counts))
        st.dataframe(city_counts)

    # 2. Demographic Analysis
    with tab2:
        st.subheader("📊 Demographic Analysis")
        col1, col2 = st.columns(2)
        age_group_counts, gender_counts = plot_demographics(filtered_data)
        with col1:
            st.write("### Age Group Distribution")
            st.bar_chart(age_group_counts.set_index('age_group'))
        with col2:
            st.write("### Gender Distribution")
            st.bar_chart(gender_counts.set_index('gender'))

    # 3. Observations & Diagnostics
    with tab3:
        st.subheader("🩺 Top Observations")
        top_10_observations, top_10_diagnostics = plot_observations(filtered_data)
        st.plotly_chart(px.bar(top_10_observations, y='Observation', x='Count', orientation='h'))
        st.table(top_10_observations)
        st.subheader("🧬 Top 10 Diagnostics")
        st.plotly_chart(px.bar(top_10_diagnostics, y='Diagnostic', x='Count', orientation='h'))
        st.table(top_10_diagnostics)

    # 4. Medicines
    with tab4:
        st.subheader("💊 Top 10 Medicines")
        top_10_medicines = plot_medicines(filtered_data)
        st.plotly_chart(px.bar(top_10_medicines, y='Medicine', x='Count', orientation='h'))
        st.table(top_10_medicines)

    # 5. Pharma Analytics
    with tab5:
        st.subheader("🏭 Top 17 Medicine Manufacturers")
        top_17_manufacturers, top_15_primary_use = plot_pharma_analytics(filtered_data)
        st.plotly_chart(px.bar(top_17_manufacturers, y='Manufacturers', x='Count', orientation='h'))
        st.subheader("🔍 Top 15 Medications Primary Use")
        st.plotly_chart(px.bar(top_15_primary_use, y='Primary Use', x='Count', orientation='h'))

if __name__ == "__main__":
    main()

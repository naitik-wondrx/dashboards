import streamlit as st
import pandas as pd
import plotly.express as px

# Load data functions
def load_data(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)

def load_state_coords(file_path):
    return pd.read_csv(file_path)

# Filtering data
def apply_filters(data, state_filter, city_filter):
    filtered_data = data.copy()
    if state_filter:
        filtered_data = filtered_data[filtered_data['state_name'].isin(state_filter)]
    if city_filter:
        filtered_data = filtered_data[filtered_data['city'].isin(city_filter)]
    return filtered_data

# Cleaning data
def clean_data(data):
    data['value'] = data['value'].str.lower().apply(lambda x: "PAIN IN ABDOMEN" if "abd" in str(x) else x)
    replacements = {
        'cbc': 'cbc',
        'urine': 'urine',
        'hbsag': 'hbsag',
    }
    for key, value in replacements.items():
        data['value'] = data['value'].str.lower().apply(lambda x: key if value in str(x) else x)
    return data

# Aggregating data
def aggregate_data(data):
    state_counts = data[data['state_name'].notna()].groupby('state_name').size().reset_index(name='count')
    city_counts = data[data['city'].notna()].groupby('city').size().reset_index(name='count')
    return state_counts.sort_values(by='count', ascending=False), city_counts.sort_values(by='count', ascending=False)

# Merging state data with coordinates
def merge_state_data(state_counts, state_coords):
    merged_state_data = pd.merge(state_counts, state_coords, on='state_name', how='left')
    return merged_state_data.dropna(subset=['latitude', 'longitude'])

# Plotting functions
def plot_bar_chart(data, x, y, title=None, orientation='v', color=None):
    return px.bar(
        data,
        x=x,
        y=y,
        orientation=orientation,
        title=title,
        color=color,
        category_orders={y: data[y].tolist()},
    )

def plot_scatter_map(data, lat, lon, size, hover,title=None):
    return px.scatter_mapbox(
        data,
        lat=lat,
        lon=lon,
        size=size,
        hover_name=hover,
        zoom=4,
        mapbox_style="carto-darkmatter",
        color='count',
        title=title,
        color_continuous_scale=px.colors.sequential.Plasma
    )

def plot_demographics(data):
    age_bins = [0, 18, 30, 40, 50, 60, 70, 100]
    age_labels = ['<18', '18-30', '30-40', '40-50', '50-60', '60-70', '70+']
    data['age_group'] = pd.cut(data['age'], bins=age_bins, labels=age_labels)

    age_group_counts = data['age_group'].value_counts().reset_index()
    age_group_counts.columns = ['age_group', 'count']

    gender_counts = data['gender'].str.upper().value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']

    return age_group_counts.sort_values(by='count', ascending=False), gender_counts.sort_values(by='count', ascending=False)

def plot_pie_chart(data, names, values, title=None):
    return px.pie(
        data,
        names=names,
        values=values,
        title=title
    )

def plot_top_items(data, column, item_type, top_n=10):
    top_items = (
        data[data['type'] == item_type][column]
        .str.upper()
        .dropna()
        .value_counts()
        .nlargest(top_n)
        .reset_index()
    )
    top_items.columns = [item_type, 'Count']
    return top_items

def plot_diagnostics_gender(data):
    diagnostics_gender = (
        data[data['type'] == 'Diagnostic']
        .dropna(subset=['value', 'gender'])
        .assign(value=lambda df: df['value'].str.upper())
        .assign(gender=lambda df: df['gender'].str.upper())
        .groupby(['value', 'gender'])
        .size()
        .reset_index(name='Count')
    )
    top_diagnostics = diagnostics_gender.groupby('value')['Count'].sum().nlargest(10).index
    diagnostics_gender = diagnostics_gender[diagnostics_gender['value'].isin(top_diagnostics)]

    return diagnostics_gender

def plot_pharma_analytics(filtered_data):
    top_15_manufacturers = (
        filtered_data['manufacturers']
        .str.upper()
        .dropna()
        .value_counts()
        .nlargest(15)
        .reset_index()
    )
    top_15_manufacturers.columns = ['Manufacturers', 'Count']

    exploded_primary_use = filtered_data['primary_use'].dropna().str.split('|', expand=True).stack().str.upper().str.strip()
    exploded_primary_use = exploded_primary_use.reset_index(level=1, drop=True).rename("Primary Use")

    top_15_primary_uses = (
        exploded_primary_use
        .value_counts()
        .nlargest(15)
        .reset_index()
    )
    top_15_primary_uses.columns = ['Primary Use', 'Count']

    return top_15_manufacturers, top_15_primary_uses

def main():
    # Load data
    st.set_page_config(layout="wide", page_title="Gynaecology Patient Data Dashboard")
    file_path = 'Consolidated_Patient_Data.xlsx'
    state_coords_path = 'state_coordinates.csv'
    data = load_data(file_path, sheet_name='Sheet1')
    state_coords = load_state_coords(state_coords_path)

    # Sidebar filters
    st.sidebar.title("Filters")
    state_filter = st.sidebar.multiselect("Select State", data['state_name'].unique())
    city_filter = st.sidebar.multiselect("Select City", data['city'].unique())

    # Data processing
    filtered_data = clean_data(apply_filters(data, state_filter, city_filter))
    state_counts, city_counts = aggregate_data(filtered_data)
    merged_state_data = merge_state_data(state_counts, state_coords)

    # App Title
    st.title("Gynaecology Patient Data Dashboard")

    # Tabs for visualization
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📍 City & State Distribution",
        "📊 Demographics",
        "🩺 Observations & Diagnostics",
        "💊 Medicines",
        "🏭 Pharma Analytics"
    ])

    # Tab 1: City & State Distribution
    with tab1:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            # st.plotly_chart(plot_scatter_map(merged_state_data, 'latitude', 'longitude', 'count', 'state_name', "Patient Distribution by City"))
            st.plotly_chart(plot_bar_chart(state_counts, 'count', 'state_name', "Patient Distribution by State", orientation='h', color='state_name'))
        with col2:
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.write("")
            st.dataframe(state_counts.reset_index(drop=True))

        col3, col4 = st.columns(2, gap="large")
        with col3:
            st.plotly_chart(plot_bar_chart(city_counts, 'count', 'city', "Patient Distribution by City", orientation='h', color='city'))
        with col4:
            st.write("")
            st.write("")
            st.write("")

            st.dataframe(city_counts.reset_index(drop=True))

    # Tab 2: Demographics
    with tab2:
        age_group_counts, gender_counts = plot_demographics(filtered_data)

        st.subheader("Age Group Distribution")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_pie_chart(age_group_counts, 'age_group', 'count'))
        with col2:
            st.dataframe(age_group_counts)

        st.subheader("Gender Distribution")
        col1, col2 = st.columns(2, gap="large")
        with col1:
           st.plotly_chart(plot_pie_chart(gender_counts, 'gender', 'count'))

        with col2:
            st.dataframe(gender_counts)
        
    # Tab 3: Observations & Diagnostics
    with tab3:
        st.subheader("Top Observations")
        top_observations = plot_top_items(filtered_data, 'value', 'Observation')
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_bar_chart(top_observations, 'Count', 'Observation', orientation='h'))
        with col2:
            st.dataframe(top_observations)

        st.subheader("Diagnostics by Gender")
        diagnostics_gender = plot_diagnostics_gender(filtered_data)
        diagnostics_gender['Total'] = diagnostics_gender.groupby('value')['Count'].transform('sum')
        diagnostics_gender = diagnostics_gender.sort_values(by='Total', ascending=False)
        
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_bar_chart(diagnostics_gender, 'Count', 'value', "Top Diagnostics by Gender", orientation='h', color='gender'))
        with col2:
            diagnostics_pivot = diagnostics_gender.pivot(index='value', columns='gender', values='Count').fillna(0)
            diagnostics_pivot['Total'] = diagnostics_pivot.sum(axis=1)
            diagnostics_pivot = diagnostics_pivot.sort_values(by='Total', ascending=False)
            st.dataframe(diagnostics_pivot)

    # Tab 4: Medicines
    with tab4:
        st.subheader("Top Medicines")
        top_medicines = plot_top_items(filtered_data, 'value', 'Medicine')
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_bar_chart(top_medicines, 'Count', 'Medicine', "Top Medicines", orientation='h'))
        with col2:
            st.dataframe(top_medicines)


    # Tab 5: Pharma Analytics
    with tab5:
        top_15_manufacturers, top_15_primary_uses = plot_pharma_analytics(filtered_data)
        st.subheader("Top Medicine Manufacturers")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            # st.plotly_chart(plot_bar_chart(top_15_manufacturers, 'Count', 'Manufacturers', orientation='h'))
            st.plotly_chart(plot_pie_chart(top_15_manufacturers, 'Manufacturers', 'Count'))
        with col2:
            top_15_manufacturers['Percentage'] = ((top_15_manufacturers['Count'] / top_15_manufacturers['Count'].sum()) * 100).round(2)
            st.dataframe(top_15_manufacturers.sort_values(by='Count', ascending=False))


        st.subheader("Top Primary Uses")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_bar_chart(top_15_primary_uses, 'Count', 'Primary Use', orientation='h'))
        with col2:
            st.dataframe(top_15_primary_uses.sort_values(by='Count', ascending=False))


if __name__ == "__main__":
    main()

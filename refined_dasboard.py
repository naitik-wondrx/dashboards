import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime



def load_data(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)

def load_state_coords(file_path):
    return pd.read_csv(file_path)
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
def apply_filters(data, state_filter, city_filter, pincode_filter):
    filtered_data = data.copy()
    if state_filter:
        filtered_data = filtered_data[filtered_data['state_name'].isin(state_filter)]
    if city_filter:
        filtered_data = filtered_data[filtered_data['city'].isin(city_filter)]
    if pincode_filter:
        filtered_data = filtered_data[filtered_data['pincode'].isin(pincode_filter)]
    return filtered_data

# Aggregating data
def aggregate_data(data):
    state_counts = data[data['state_name'].notna()].groupby('state_name').size().reset_index(name='count')
    city_counts = data[data['city'].notna()].groupby('city').size().reset_index(name='count')
    return state_counts.sort_values(by='count', ascending=False), city_counts.sort_values(by='count', ascending=False)

# Merging state data with coordinates
def merge_state_data(state_counts, state_coords):
    merged_state_data = pd.merge(state_counts, state_coords, on='state_name', how='left')
    return merged_state_data.dropna(subset=['latitude', 'longitude'])


def visualize_data_types(tab, data):
    with tab:
        st.subheader("Distribution of Data Types")

        # Count occurrences of each type
        type_counts = data['type'].str.capitalize().value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']

        col1, col2 = st.columns(2)
        with col1:
            # Plot the data type distribution
            st.plotly_chart(plot_pie_chart(type_counts, 'Type', 'Count', "Data Type Distribution"))
        with col2:
            # Display the data in a table
            st.dataframe(type_counts)
        

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
        height=700 
    )

def plot_demographics(data):
    age_bins = [0, 18, 25, 30, 40, 50, 60, 70, 100]
    age_labels = ['<18', '18-25', '25-30', '30-40', '40-50', '50-60', '60-70', '70+']
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

def plot_observation_gender(data):
    observation_gender = (
        data[data['type'] == 'Observation']
        .dropna(subset=['value', 'gender'])
        .assign(value=lambda df: df['value'].str.upper())
        .assign(gender=lambda df: df['gender'].str.upper())
        .groupby(['value', 'gender'])
        .size()
        .reset_index(name='Count')
    )
    top_observation = observation_gender.groupby('value')['Count'].sum().nlargest(10).index
    observation_gender = observation_gender[observation_gender['value'].isin(top_observation)]

    return observation_gender

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

def visualize_patient_data(tab, filtered_patient_data):
    with tab:
        state_counts, city_counts = aggregate_data(filtered_patient_data)

        st.subheader("Patient Distribution by State")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_bar_chart(state_counts, 'count', 'state_name', orientation='h'))
        with col2:
            st.dataframe(state_counts.sort_values(by='count', ascending=False).reset_index(drop=True))

        st.subheader("Patient Distribution by City")
        col3, col4 = st.columns(2, gap="large")
        with col3:
            st.plotly_chart(plot_bar_chart(city_counts, 'count', 'city', orientation='h'))
        with col4:
            st.dataframe(city_counts.sort_values(by='count', ascending=False).reset_index(drop=True))

def visualize_patient_demographics(tab, filtered_patient_data):
    with tab:
        age_group_counts, gender_counts = plot_demographics(filtered_patient_data)
        age_group_counts = age_group_counts.sort_values('age_group')

        st.subheader("Age Group Distribution")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_pie_chart(age_group_counts, 'age_group', 'count'))
        with col2:
            st.dataframe(age_group_counts.sort_values(by='age_group', ascending=True).reset_index(drop=True))

        st.subheader("Gender Distribution")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_pie_chart(gender_counts, 'gender', 'count'))
        with col2:
            st.dataframe(gender_counts)

def visualize_observations(tab, data):
    with tab:
        st.subheader("Top Observations")
        top_observations = plot_top_items(data, 'value', 'Observation')
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_bar_chart(top_observations, 'Count', 'Observation', orientation='h'))
        with col2:
            st.dataframe(top_observations)
        
        st.subheader("Observations by Gender")
        observations_gender = plot_observation_gender(data)
        observations_gender['Total'] = observations_gender.groupby('value')['Count'].transform('sum')
        observations_gender = observations_gender.sort_values(by='Total', ascending=False)

        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_bar_chart(observations_gender, 'Count', 'value', "Top Observations by Gender", orientation='h', color='gender'))
        with col2:
            observations_pivot = observations_gender.pivot(index='value', columns='gender', values='Count').fillna(0)
            observations_pivot['Total'] = observations_pivot.sum(axis=1)
            observations_pivot = observations_pivot.sort_values(by='Total', ascending=False)
            st.dataframe(observations_pivot)

def visualize_diagnostics(tab, data):
    with tab:
        st.subheader("Top Diagnostics")
        top_diagnostics = plot_top_items(data, 'value', 'Diagnostic')
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.plotly_chart(plot_bar_chart(top_diagnostics, 'Count', 'Diagnostic', orientation='h'))
        with col2:
            st.dataframe(top_diagnostics)


        st.subheader("Diagnostics by Gender")
        diagnostics_gender = plot_diagnostics_gender(data)
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

def visualize_gynac_medicines(tab, filtered_gynac_data):
    with tab:
        st.subheader("Top Medicines")
        top_medicines = plot_top_items(filtered_gynac_data, 'value', 'Medicine', top_n=20)
        st.plotly_chart(plot_bar_chart(top_medicines, 'Count', 'Medicine', orientation='h'))

def visualize_pharma_analytics(tab, filtered_gynac_data):
    with tab:
        top_15_manufacturers, top_15_primary_uses = plot_pharma_analytics(filtered_gynac_data)

        st.subheader("Top Manufacturers")
        st.plotly_chart(plot_pie_chart(top_15_manufacturers, 'Manufacturers', 'Count'))

        st.subheader("Top Primary Uses")
        st.plotly_chart(plot_bar_chart(top_15_primary_uses, 'Count', 'Primary Use', orientation='h'))

def visualize_manufacturer_medicines(tab, data):
    with tab:
        st.subheader("Medicines by Manufacturer")
        top_15_manufacturers, _ = plot_pharma_analytics(data)

        
        # Dropdown for selecting a manufacturer
        # manufacturers = data['manufacturers'].dropna().unique().nlargest(10)
        top_15_manufacturers = top_15_manufacturers['Manufacturers'].tolist()
        selected_manufacturer = st.selectbox("Select Manufacturer", top_15_manufacturers)

        if selected_manufacturer:
            # Filter data for the selected manufacturer
            manufacturer_data = data[data['manufacturers'].str.upper() == selected_manufacturer]

            # Count medicines made by the manufacturer
            medicine_counts = (
                manufacturer_data[manufacturer_data['type'] == 'Medicine']['value']
                .dropna()
                .str.upper()
                .value_counts()
                .nlargest(10)
                .reset_index()
            )
            medicine_counts.columns = ['Medicine', 'Count']

            col1, col2 = st.columns(2, gap="large")

            with col1:
                # Plot pie chart
                st.plotly_chart(plot_pie_chart(medicine_counts, 'Medicine', 'Count', f"Medicines by {selected_manufacturer}"))

            with col2:
                # Display data table
                st.dataframe(medicine_counts)
def display_totals(filtered_data):
    st.sidebar.markdown("### Totals in Analytics")
    total_doctors = filtered_data['doctor_id'].nunique()
    total_patients = filtered_data['ptp_id'].nunique()
    st.sidebar.metric("Total Doctors", total_doctors)
    st.sidebar.metric("Total Patients", total_patients)

def filter_by_date(data, start_date, end_date):
    data['start_time']=pd.to_datetime(data['start_time']).dt.date
    return data[(data['start_time'] >= start_date) & (data['start_time'] <= end_date)]
def manufacturer_comparison_tab(tab, data):
    with tab:
        st.subheader("Manufacturer Comparison")

        # Select manufacturers to compare
        manufacturers = data['manufacturers'].unique()
        selected_manufacturers = st.multiselect("Select Manufacturers for Comparison", manufacturers)

        if not selected_manufacturers:
            st.info("Select at least one manufacturer to view the comparison.")
            return

        # Filter data for selected manufacturers
        filtered_data = data[data['manufacturers'].isin(selected_manufacturers)]

        # Display data for each manufacturer
        columns = st.columns(len(selected_manufacturers))
        for i, manufacturer in enumerate(selected_manufacturers):
            with columns[i]:
                st.write(f"### {manufacturer}")
                manufacturer_data = filtered_data[filtered_data['manufacturers'] == manufacturer]

                # Group by medicine and calculate metrics
                metrics = (
                    manufacturer_data.groupby('value')
                    .agg(
                        Unique_Patients=('ptp_id', 'nunique'),
                        Total=('ptp_id', 'count'),
                    )
                    .reset_index()
                )
                metrics['%GT Count'] = (metrics['Total'] / metrics['Total'].sum() * 100).round(2)

                # Display table
                st.dataframe(metrics.drop(['Total'],axis=1).sort_values(by='Unique_Patients', ascending=False).reset_index(drop=True))

def visualize_vitals(tab, data):
    """
    Creates a tab for displaying the distribution of vitals for patients.
    """
    with tab:
        st.subheader("Vitals Distribution")

        # List of vitals to include
        vitals = [
            'Blood pressure (BP)', 'Height', 'Oxygen saturation (SpO2)', 
            'Pulse', 'Random Blood Sugar (RBS)', 'Respiration rate', 
            'Temperature', 'Weight'
        ]

        # Check if all vitals are present in the dataset
        available_vitals = [vital for vital in vitals if vital in data.columns]

        if not available_vitals:
            st.warning("No vital columns found in the dataset.")
            return

        # Display a toggle for each vital
        for vital in available_vitals:
            with st.expander(f"Show Distribution for {vital}", expanded=False):
                # Filter non-NaN values for the vital
                vital_data = data[vital].dropna()

                if vital_data.empty:
                    st.info(f"No data available for {vital}.")
                    continue

                # Histogram for the vital
                fig = px.histogram(
                    vital_data,
                    x=vital,
                    title=f"Distribution of {vital}",
                    nbins=20,
                    labels={vital: vital},
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Optional: Display basic statistics
                st.write(f"**Statistics for {vital}:**")
                st.write(vital_data.describe())
def visualize_value_comparison(tab, data):
    """
    Creates a tab for value-based comparison of manufacturers.
    """
    with tab:
        st.subheader("Value-Based Manufacturer Comparison")

        # Group data by manufacturers
        manufacturer_comparison = (
            data.groupby('manufacturers')
            .agg(
                Total_Value=('min_mrp', 'sum'),  # Replace with relevant column
                Average_Value=('min_mrp', 'mean'),  # Replace with relevant column
                Patient_Count=('ptp_id', 'nunique')
            )
            .reset_index()
        )

        # Sort by Total Value
        manufacturer_comparison = manufacturer_comparison.sort_values(by='Total_Value', ascending=False)

        # Create toggles for viewing different metrics
        toggle_option = st.radio(
            "Select Metric to Compare:",
            options=['Total Value', 'Average Value', 'Patient Count'],
            horizontal=True
        )

        # Display the selected metric as a bar chart
        if toggle_option == 'Total Value':
            fig = px.bar(
                manufacturer_comparison,
                x='manufacturers',
                y='Total_Value',
                title="Total Value by Manufacturer",
                labels={'Total_Value': 'Total Value'},
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        elif toggle_option == 'Average Value':
            fig = px.bar(
                manufacturer_comparison,
                x='manufacturers',
                y='Average_Value',
                title="Average Value by Manufacturer",
                labels={'Average_Value': 'Average Value'},
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        elif toggle_option == 'Patient Count':
            fig = px.bar(
                manufacturer_comparison,
                x='manufacturers',
                y='Patient_Count',
                title="Patient Count by Manufacturer",
                labels={'Patient_Count': 'Patient Count'},
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Display the data as a table
        st.dataframe(manufacturer_comparison.reset_index(drop=True))

def main():
    # Set page configuration
    st.set_page_config(layout="wide", page_title="Gynaecology Patient Data Dashboard")
    logo_path = 'logo.png'
    st.image(logo_path, width=150)

    # File paths
    patient_file = 'Consolidated_lupin-digitization.xlsx'
    gynac_file = 'lupin-digitization.xlsx'

    # Load datasets
    patient_data = load_data(patient_file, sheet_name='Sheet1')
    gynac_data = load_data(gynac_file, sheet_name='Result 1')

    # Sidebar filters for patient data
    st.sidebar.title("Filters for Patient Data")
    state_filter = st.sidebar.multiselect("Select State", patient_data['state_name'].unique())
    city_filter = st.sidebar.multiselect("Select City", patient_data['city'].unique())
    # company_filter = st.sidebar.multiselect("Select Company", patient_data['company'].unique())
    pincode_filter = st.sidebar.multiselect("Select Pincode", patient_data['pincode'].unique())
    start_date, end_date = st.sidebar.date_input(
        "Analytics Time Period",
        value=(datetime(2020, 1, 1), datetime.today()),
        key="analytics_time_period",
    )
    # Filter patient data
    filtered_patient_data = filter_by_date(apply_filters(patient_data, state_filter, city_filter, pincode_filter), start_date, end_date)
    filtered_gynac_data = filter_by_date(clean_data(apply_filters(gynac_data, state_filter, city_filter, pincode_filter)), start_date, end_date)

    # Sidebar filters for gynecology data

    # App Title
    st.title("Gynaecology Patient Data Dashboard")

    # Visualization Tabs
    tab1, tab2, tab3, tab4,tab5,tab6,tab7,tab8,tab9,tab10,tab11  = st.tabs([
        "📂 Data Types",
        "📍 Patient Data Distribution",
        "📊 Patient Demographics",
        "💊 Gynac Medicines",
        "🏭 Pharma Analytics",
        "🩺 Observations",
        "🧪 Diagnostics",
        "🏷️ Manufacturer Medicines",
        "🔍 Manufacturer Comparison",
        "🩺 Vitals",
        "💰 Value-Based Comparison"
    ])
    st.sidebar.download_button(
        label="Export Data as CSV",
        data=filtered_gynac_data.to_csv(index=False),
        file_name="filtered_data.csv",
        mime="text/csv",
    )


    # Visualizations for each tab
    display_totals(filtered_patient_data)
    visualize_data_types(tab1, filtered_gynac_data)
    visualize_patient_data(tab2, filtered_patient_data)
    visualize_patient_demographics(tab3, filtered_patient_data)
    visualize_gynac_medicines(tab4, filtered_gynac_data)
    visualize_pharma_analytics(tab5, filtered_gynac_data)
    visualize_observations(tab6, filtered_gynac_data)
    visualize_diagnostics(tab7, filtered_gynac_data)
    visualize_manufacturer_medicines(tab8, filtered_gynac_data)
    manufacturer_comparison_tab(tab9, filtered_gynac_data)
    visualize_vitals(tab10, filtered_patient_data)
    visualize_value_comparison(tab11, filtered_gynac_data)

if __name__ == "__main__":
    main()

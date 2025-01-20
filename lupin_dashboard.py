import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime


@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)
    # The file_path parameter can be a URL. No additional code needed.

def load_state_coordinates(file_path):
    return pd.read_csv(file_path)

def clean_medical_data(data):
    data['average_mrp'] = data[['min_mrp', 'max_mrp']].mean(axis=1).round(2)
    data['value'] = data['value'].str.lower().apply(lambda x: "pain in abdomen" if "pain in abd" in str(x) else x)
    replacements = {
        'cbc': 'cbc',
        'urine': 'urine',
        'hbsag': 'hbsag',
    }
    for key, value in replacements.items():
        data['value'] = data['value'].str.lower().apply(lambda x: key if value in str(x) else x)
    return data

def apply_filters(data, state_filter=None, city_filter=None, pincode_filter=None, speciality_filter=None):
    filtered_data = data.copy()
    if state_filter:
        filtered_data = filtered_data[filtered_data['state_name'].isin(state_filter)]
    if city_filter:
        filtered_data = filtered_data[filtered_data['city'].isin(city_filter)]
    if pincode_filter:
        filtered_data = filtered_data[filtered_data['pincode'].str.split(',').apply(lambda x: any(p.strip() in pincode_filter for p in x))]
    if speciality_filter:
        filtered_data = filtered_data[filtered_data['speciality'].isin(speciality_filter)]
    return filtered_data

def filter_by_date_range(data, start_date, end_date):
    data['start_time'] = pd.to_datetime(data['start_time']).dt.date
    return data[(data['start_time'] >= start_date) & (data['start_time'] <= end_date)]

def display_sidebar_totals(filtered_data):
    st.sidebar.markdown("### Totals in Analytics")
    total_doctors = filtered_data['doctor_id'].nunique()
    total_patients = filtered_data['id'].nunique()
    st.sidebar.metric("Total Doctors", total_doctors)
    st.sidebar.metric("Total Patients", total_patients)

def aggregate_geo_data(data, group_by_column, count_column):
    aggregated_data = data.groupby(group_by_column)[count_column].nunique().reset_index()
    aggregated_data.columns = [group_by_column, 'count']
    aggregated_data = aggregated_data.sort_values(by='count', ascending=False)
    return aggregated_data

def create_bar_chart(data, x_column, y_column, title=None, orientation='v', color=None, text=None):
    return px.bar(
        data,
        x=x_column,
        y=y_column,
        orientation=orientation,
        title=title,
        color=color,
        category_orders={y_column: data[y_column].tolist()},
        height=700,
        text=text,
    )

def prepare_demographics(data):
    age_bins = [0, 18, 25, 30, 40, 50, 60, 70, 100]
    age_labels = ['<18', '18-25', '25-30', '30-40', '40-50', '50-60', '60-70', '70+']
    data['age_group'] = pd.cut(data['age'], bins=age_bins, labels=age_labels)

    age_group_counts = data['age_group'].value_counts().reset_index()
    age_group_counts.columns = ['age_group', 'count']

    gender_counts = data['gender'].str.upper().value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']

    return age_group_counts.sort_values(by='count', ascending=False), gender_counts.sort_values(by='count', ascending=False)

def create_pie_chart(data, names_column, values_column, title=None,color_map=None):
      # Define color mapping for FEMALE and MALE
    return px.pie(
        data,
        names=names_column,
        values=values_column,
        title=title,
        color=names_column,  # Specify the column for color mapping
        color_discrete_map=color_map  # Apply the color mapping
    )

def get_top_items(data, value_column, item_type):
    top_items = (
        data[data['type'] == item_type][value_column]
        .str.upper()
        .dropna()
        .value_counts()
        .reset_index()
    )
    top_items.columns = [item_type, 'count']
    return top_items

def analyze_observation_by_gender(data):
    observation_gender = (
        data[data['type'] == 'Observation']
        .dropna(subset=['value', 'gender'])
        .assign(value=lambda df: df['value'].str.upper())
        .assign(gender=lambda df: df['gender'].str.upper())
        .groupby(['value', 'gender'])
        .size()
        .reset_index(name='count')
    )
    observation_gender['total'] = observation_gender.groupby('value')['count'].transform('sum')
    observation_gender = observation_gender.sort_values(by='total', ascending=False).drop('total', axis=1)

    return observation_gender

def analyze_diagnostics_by_gender(data):
    diagnostics_gender = (
        data[data['type'] == 'Diagnostic']
        .dropna(subset=['value', 'gender'])
        .assign(value=lambda df: df['value'].str.upper())
        .assign(gender=lambda df: df['gender'].str.upper())
        .groupby(['value', 'gender'])
        .size()
        .reset_index(name='count')
    )
    diagnostics_gender['total'] = diagnostics_gender.groupby('value')['count'].transform('sum')
    diagnostics_gender = diagnostics_gender.sort_values(by='total', ascending=False).drop('total', axis=1)

    return diagnostics_gender

def analyze_pharma_data(filtered_data):
    """
    Analyze pharma data to extract top manufacturers and primary uses.
    Handles cases where data is missing or invalid.
    """
    # Fill missing values in primary_use with an empty string for processing
    filtered_data['primary_use'] = filtered_data['primary_use'].fillna("").astype(str)

    # Top manufacturers (always calculated if manufacturers are present)
    if not filtered_data['manufacturers'].dropna().empty:
        top_manufacturers = (
            filtered_data['manufacturers']
            .str.upper()
            .dropna()
            .value_counts()
            .reset_index()
        )
        top_manufacturers.columns = ['manufacturers', 'count']
    else:
        top_manufacturers = pd.DataFrame(columns=['manufacturers', 'count'])

    # Explode primary_use for detailed analysis
    filtered_primary_use = filtered_data[filtered_data['primary_use'].str.strip() != ""]
    if not filtered_primary_use.empty:
        exploded_primary_use = (
            filtered_primary_use['primary_use']
            .str.split('|', expand=True)
            .stack()
            .str.upper()
            .str.strip()
        )
        if not exploded_primary_use.empty:
            top_primary_uses = (
                exploded_primary_use
                .reset_index(level=1, drop=True)
                .rename("primary_use")
                .value_counts()
                .reset_index()
            )
            top_primary_uses.columns = ['primary_use', 'count']
        else:
            top_primary_uses = pd.DataFrame(columns=['primary_use', 'count'])
    else:
        top_primary_uses = pd.DataFrame(columns=['primary_use', 'count'])

    return top_manufacturers, top_primary_uses



def visualize_data_types(tab, data):
    with tab:
        with st.expander("Distribution of Data Types within Rx"):
            type_counts = data['type'].str.capitalize().value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']

            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(create_pie_chart(type_counts, 'Type', 'Count'))
            with col2:
                st.dataframe(type_counts)
        with st.expander("Distribution of Speciality Doctors"):
            speciality_counts = data.groupby('speciality')['doctor_id'].nunique().reset_index()
            speciality_counts.columns = ['Speciality', 'Count']

            col1, col2 = st.columns([2, 1])
            with col1:
                st.plotly_chart(create_pie_chart(speciality_counts, 'Speciality', 'Count'))
            with col2:
                st.dataframe(speciality_counts.sort_values(by='Count', ascending=False).reset_index(drop=True))

def visualize_geographical_distribution(tab, data):
    with tab:
        with st.expander("Patient Distribution by State"):
            patient_state_counts = aggregate_geo_data(data, 'state_name', 'id')
            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(
                    create_bar_chart(patient_state_counts.head(15), 'count', 'state_name', orientation='h', text='count',color='count'),
                    use_container_width=True,
                    key="patient_state_chart"
                )
            with col2:
                st.dataframe(patient_state_counts.reset_index(drop=True), key="patient_state_table")

        with st.expander("Patient Distribution by City"):
            patient_city_counts = aggregate_geo_data(data, 'city', 'id')
            col3, col4 = st.columns([3, 1])
            with col3:
                st.plotly_chart(
                    create_bar_chart(patient_city_counts.head(25), 'count', 'city', orientation='h', text='count',color='count'),
                    use_container_width=True,
                    key="patient_city_chart"
                )
            with col4:
                st.dataframe(patient_city_counts.reset_index(drop=True), key="patient_city_table")

        with st.expander("Doctor Distribution by State"):
            doctor_state_counts = aggregate_geo_data(data, 'state_name', 'doctor_id')
            col5, col6 = st.columns([3, 1])
            with col5:
                st.plotly_chart(
                    create_bar_chart(doctor_state_counts.head(15), 'count', 'state_name', orientation='h', text='count',color='count'),
                    use_container_width=True,
                    key="doctor_state_chart"
                )
            with col6:
                st.dataframe(doctor_state_counts.reset_index(drop=True), key="doctor_state_table")

        with st.expander("Doctor Distribution by City"):
            doctor_city_counts = aggregate_geo_data(data, 'city', 'doctor_id')
            col7, col8 = st.columns([3, 1])
            with col7:
                st.plotly_chart(
                    create_bar_chart(doctor_city_counts.head(25), 'count', 'city', orientation='h', text='count',color='count'),
                    use_container_width=True,
                    key="doctor_city_chart"
                )
            with col8:
                st.dataframe(doctor_city_counts.reset_index(drop=True), key="doctor_city_table")

def visualize_patient_demographics(tab, data):
    with tab:
        data = data.drop_duplicates(subset=['id'])
        age_group_counts, gender_counts = prepare_demographics(data)
        age_group_counts = age_group_counts.sort_values('age_group')

        with st.expander("Age Group Distribution of Patients"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(create_pie_chart(age_group_counts, 'age_group', 'count'))
            with col2:
                st.dataframe(age_group_counts.sort_values(by='age_group', ascending=True).reset_index(drop=True))

        with st.expander("Gender Distribution of Patients"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(create_pie_chart(gender_counts, 'gender', 'count',color_map = {'FEMALE': '#FF69B4', 'MALE': '#0F52BA'}))
            with col2:
                st.dataframe(gender_counts)

def visualize_medicines(tab, filtered_medical_data):
    with tab:
        with st.expander("Top Medicines"):
            top_medicines = get_top_items(filtered_medical_data, 'value', 'Medicine')
            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(create_bar_chart(top_medicines.head(20), 'count', 'Medicine', orientation='h', text='count',color='count'))
            with col2:
                st.dataframe(top_medicines)
        
        # Clean and explode primary use data

        with st.expander("Top Medicines by Primary Use"):

            filtered_medical_data['primary_use'] = filtered_medical_data['primary_use'].fillna("").astype(str)
            exploded_data = filtered_medical_data.copy()
            exploded_data = exploded_data[exploded_data['primary_use'].str.strip() != ""]
            exploded_data = exploded_data.assign(
                exploded_primary_use=exploded_data['primary_use'].str.split('|')
            ).explode('exploded_primary_use')
            exploded_data['exploded_primary_use'] = exploded_data['exploded_primary_use'].str.strip().str.upper()

            # Get unique primary uses for selection
            unique_primary_uses = exploded_data['exploded_primary_use'].dropna().unique()
            selected_primary_use = st.selectbox("Select Primary Use", unique_primary_uses, key="primary_use_select")

            if not selected_primary_use:
                st.info("Please select a primary use to view top medicines.")
                return

            # Filter data for the selected primary use
            filtered_data = exploded_data[exploded_data['exploded_primary_use'] == selected_primary_use]

            # Group by medicine and calculate counts
            top_medicines = (
                filtered_data[filtered_data['type'] == 'Medicine']
                .groupby('value')
                .size()
                .reset_index(name='count')
                .sort_values(by='count', ascending=False)
            )

            # Display chart and table
            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(
                    create_bar_chart(top_medicines.head(10), 'count', 'value', orientation='h', text='count', title=f"Top Medicines for {selected_primary_use}"),
                    use_container_width=True,
                    key="top_medicines_chart"
                )
            with col2:
                st.dataframe(top_medicines.head(10).reset_index(drop=True))

def visualize_pharma_analytics(tab, filtered_medical_data):
    with tab:
        top_15_manufacturers, top_15_primary_uses = analyze_pharma_data(filtered_medical_data)
        

        with st.expander("Top Manufacturers"):
            if top_15_manufacturers is not None and not top_15_manufacturers.empty:
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.plotly_chart(create_pie_chart(top_15_manufacturers.head(15), 'manufacturers', 'count'))
                with col2:
                    st.dataframe(top_15_manufacturers)
            else:
                st.warning("No data available for Top Manufacturers.")

        with st.expander("Top Primary Uses"):
            if top_15_primary_uses is not None and not top_15_primary_uses.empty:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.plotly_chart(create_bar_chart(top_15_primary_uses.head(15), 'count', 'primary_use', orientation='h', text='count', color='count'))
                with col2:
                    st.dataframe(top_15_primary_uses)
            else:
                st.warning("No data available for Top Primary Uses.")

def visualize_observations(tab, data):
    with tab:
        with st.expander("Top Observations"):
            top_observations = get_top_items(data, 'value', 'Observation')
            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(create_bar_chart(top_observations.head(20), 'count', 'Observation', orientation='h', text='count',color='count'))
            with col2:
                st.dataframe(top_observations)

        with st.expander("Observations by Gender"):
            observations_gender = analyze_observation_by_gender(data)
            observations_gender['Total'] = observations_gender.groupby('value')['count'].transform('sum')
            observations_gender = observations_gender.sort_values(by='Total', ascending=False)
            observations_pivot = observations_gender.pivot(index='value', columns='gender', values='count').fillna(0)
            observations_pivot['Total'] = observations_pivot.sum(axis=1)
            observations_pivot = observations_pivot.sort_values(by='Total', ascending=False)

            col1, col2 = st.columns([70, 30])
            with col1:
                st.plotly_chart(create_bar_chart(
                    observations_pivot.head(20).reset_index().drop(columns='Total').melt(id_vars='value', var_name='gender', value_name='count'),
                    'count',
                    'value',
                    orientation='h',
                    color='gender',
                    text='count'
                ))
            with col2:
                st.dataframe(observations_pivot)

def visualize_diagnostics(tab, data):
    with tab:
        with st.expander("Top Diagnostics"):
            top_diagnostics = get_top_items(data, 'value', 'Diagnostic')
            col1, col2 = st.columns([3, 1])
            with col1:
                st.plotly_chart(
                    create_bar_chart(top_diagnostics.head(20), 'count', 'Diagnostic', orientation='h', text='count',color='count'),
                    use_container_width=True,
                    key="top_diagnostics_chart"
                )
            with col2:
                st.dataframe(top_diagnostics, key="top_diagnostics_table")

        with st.expander("Diagnostics by Gender"):
            diagnostics_gender = analyze_diagnostics_by_gender(data)
            diagnostics_gender['Total'] = diagnostics_gender.groupby('value')['count'].transform('sum')
            diagnostics_gender = diagnostics_gender.sort_values(by='Total', ascending=False)
            diagnostics_pivot = diagnostics_gender.pivot(index='value', columns='gender', values='count').fillna(0)
            diagnostics_pivot['Total'] = diagnostics_pivot.sum(axis=1)
            diagnostics_pivot = diagnostics_pivot.sort_values(by='Total', ascending=False)

            col1, col2 = st.columns([70, 30])
            with col1:
                st.plotly_chart(
                    create_bar_chart(
                        diagnostics_pivot.head(15).reset_index().drop(columns='Total').melt(id_vars='value', var_name='gender', value_name='count'),
                        'count',
                        'value',
                        orientation='h',
                        color='gender',
                        text='count'
                    ),
                    use_container_width=True,
                    key="diagnostics_by_gender_chart"
                )
            with col2:
                st.dataframe(diagnostics_pivot, key="diagnostics_by_gender_table")

def visualize_manufacturer_medicines(tab, data):
    with tab:
        st.subheader("Medicines by Manufacturer")
        top_15_manufacturers, _ = analyze_pharma_data(data)

        if top_15_manufacturers is not None and not top_15_manufacturers.empty:
            top_manufacturers_list = top_15_manufacturers['manufacturers'].tolist()
            default_index = top_manufacturers_list.index("LUPIN LTD") if "LUPIN LTD" in top_manufacturers_list else 0
            selected_manufacturer = st.selectbox(
            "Select Manufacturer",
            top_manufacturers_list,
            index=default_index
            )

            if selected_manufacturer:
                manufacturer_data = data[data['manufacturers'].str.upper() == selected_manufacturer]

            medicine_counts = (
                manufacturer_data[manufacturer_data['type'] == 'Medicine']['value']
                .dropna()
                .str.upper()
                .value_counts()
                .reset_index()
            )
            medicine_counts.columns = ['Medicine', 'Count']

            col1, col2 = st.columns([3, 1])

            with col1:
                st.plotly_chart(create_pie_chart(medicine_counts.head(10), 'Medicine', 'Count', f"Medicines by {selected_manufacturer}"))

            with col2:
                st.dataframe(medicine_counts)
        else:
            st.warning("No manufacturer data available.")

def manufacturer_comparison_tab(tab, data):
    with tab:
        st.subheader("Manufacturer Comparison")

        # Select manufacturers to compare
        manufacturers = data['manufacturers'].dropna().unique()
        selected_manufacturers = st.multiselect("Select Manufacturers for Comparison", manufacturers)

        if not selected_manufacturers:
            st.info("Select at least one manufacturer to view the comparison.")
            return

        # Filter data for selected manufacturers
        filtered_data = data[data['manufacturers'].isin(selected_manufacturers)]
        filtered_data = filtered_data[filtered_data['primary_use'].str.strip() != ""]

        # Explode the primary_use column into multiple rows
        exploded_data = filtered_data.copy()
        exploded_data = exploded_data.dropna(subset=['primary_use'])
        exploded_data = exploded_data.assign(
            exploded_primary_use=exploded_data['primary_use'].str.split('|')
        ).explode('exploded_primary_use')
        exploded_data['exploded_primary_use'] = exploded_data['exploded_primary_use'].str.strip().str.upper()

        # Get unique primary uses for selection
        unique_primary_uses = exploded_data['exploded_primary_use'].dropna().unique()
        selected_primary_uses = st.multiselect("Select Primary Uses for Comparison", unique_primary_uses)

        if not selected_primary_uses:
            st.info("Select at least one primary use to view the comparison.")
            return

        # Filter data for selected primary uses
        filtered_data = exploded_data[exploded_data['exploded_primary_use'].isin(selected_primary_uses)]

        # Display data for each manufacturer and primary use
        for manufacturer in selected_manufacturers:
            st.write(f"### {manufacturer}")
            manufacturer_data = filtered_data[filtered_data['manufacturers'] == manufacturer]

            for primary_use in selected_primary_uses:
                st.write(f"**Primary Use: {primary_use}**")
                use_data = manufacturer_data[manufacturer_data['exploded_primary_use'] == primary_use]

                # Group by medicine and calculate metrics
                metrics = (
                    use_data.groupby('value')
                    .agg(
                        Unique_Patients=('id', 'nunique'),
                        Total=('id', 'count'),
                    )
                    .reset_index()
                )
                metrics['%GT Count'] = (metrics['Total'] / metrics['Total'].sum() * 100).round(2)

                # Display table
                if not metrics.empty:
                    st.dataframe(
                        metrics.drop(['Total'], axis=1)
                        .sort_values(by='Unique_Patients', ascending=False)
                        .reset_index(drop=True)
                    )
                else:
                    st.write("No data available for this primary use.")

def visualize_market_share_primary_use(tab, data):
    with tab:
        st.subheader("Market Share Comparison by Manufacturers for a Primary Use")

        # Explode the primary_use column into multiple rows
        exploded_data = data.copy()
        exploded_data = exploded_data.dropna(subset=['primary_use'])
        exploded_data = exploded_data.assign(
            exploded_primary_use=exploded_data['primary_use'].str.split('|')
        ).explode('exploded_primary_use')
        exploded_data['exploded_primary_use'] = exploded_data['exploded_primary_use'].str.strip().str.upper()

        # Get unique primary uses for selection and remove blanks
        unique_primary_uses = exploded_data['exploded_primary_use']
        unique_primary_uses = unique_primary_uses[unique_primary_uses != ""].unique()

        selected_primary_use = st.selectbox("Select Primary Use", unique_primary_uses)

        if not selected_primary_use:
            st.info("Select a primary use to view the market share comparison.")
            return

        # Filter data for the selected primary use
        filtered_data = exploded_data[exploded_data['exploded_primary_use'] == selected_primary_use]

        # Calculate the market share of each manufacturer
        manufacturer_market_share = (
            filtered_data.groupby('manufacturers')
            .agg(Medicine_Count=('value', 'count'))
            .reset_index()
        )
        manufacturer_market_share['Market_Share_Percentage'] = (
            manufacturer_market_share['Medicine_Count'] / manufacturer_market_share['Medicine_Count'].sum() * 100
        ).round(2)

        # Sort and prepare data for the pie chart
        manufacturer_market_share = manufacturer_market_share.sort_values(
            by='Market_Share_Percentage', ascending=False
        ).reset_index(drop=True)

        # Display pie chart and data
        st.subheader(f"Primary Use: {selected_primary_use}")
        if not manufacturer_market_share.empty:
            fig = px.pie(
                manufacturer_market_share.head(20),
                names='manufacturers',
                values='Market_Share_Percentage',
                title=f"Market Share of Manufacturers for {selected_primary_use}",
                hole=0.4, hover_data=['Medicine_Count'],
            )
            col1, col2 = st.columns([2, 1])
            with col1:
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.dataframe(manufacturer_market_share)
        else:
            st.warning("No data available for the selected primary use.")

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
                Total_Value=('average_mrp', 'sum'),  # Replace with relevant column
                Average_Value=('average_mrp', 'mean'),  # Replace with relevant column
                Patient_Count=('id', 'nunique')
            )
            .reset_index()
        )

        # Get top 20 for charts
        top_20 = manufacturer_comparison.sort_values(by='Total_Value', ascending=False).head(20)

        # Create toggles for viewing different metrics
        toggle_option = st.radio(
            "Select Metric to Compare:",
            options=['Total Value', 'Average Value', 'Patient Count'],
            horizontal=True
        )

        # Display the selected metric as a bar chart
        if toggle_option == 'Total Value':
            top_20 = manufacturer_comparison.sort_values(by='Total_Value', ascending=False).head(20)

            fig = px.bar(
                top_20,
                x='manufacturers',
                y='Total_Value',
                title="Total Value by Manufacturer",
                labels={'Total_Value': 'Total Value'},
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
        

        elif toggle_option == 'Average Value':
            top_20 = manufacturer_comparison.sort_values(by='Average_Value', ascending=False).head(20)
            fig = px.bar(
                top_20,
                x='manufacturers',
                y='Average_Value',
                title="Average Value by Manufacturer",
                labels={'Average_Value': 'Average Value'},
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

        elif toggle_option == 'Patient Count':
            top_20 = manufacturer_comparison.sort_values(by='Patient_Count', ascending=False).head(20)
            fig = px.bar(
                top_20,
                x='manufacturers',
                y='Patient_Count',
                title="Patient Count by Manufacturer",
                labels={'Patient_Count': 'Patient Count'},
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Display the data as a table
        st.dataframe(
        manufacturer_comparison
        .sort_values(by='Total_Value',ascending=False).reset_index(drop=True)
        .assign(
            Total_Value_Percentage=lambda df: (df['Total_Value'] / df['Total_Value'].sum() * 100).round(2),
            Patient_Count_Percentage=lambda df: (df['Patient_Count'] / df['Patient_Count'].sum() * 100).round(2))
        )
def get_state_filter(medical_data):
    return st.sidebar.multiselect(
        "Select State",
        options=medical_data['state_name'].dropna().unique(),
        key="state_filter"
    )

def get_city_filter(medical_data, state_filter):
    if state_filter:
        filtered_cities = medical_data[medical_data['state_name'].isin(state_filter)]['city'].dropna().unique()
    else:
        filtered_cities = medical_data['city'].dropna().unique()
    return st.sidebar.multiselect(
        "Select City",
        options=filtered_cities,
        key="city_filter"
    )

def get_pincode_filter(medical_data, state_filter, city_filter):
    filtered_pincode_data = medical_data.copy()
    if state_filter:
        filtered_pincode_data = filtered_pincode_data[filtered_pincode_data['state_name'].isin(state_filter)]
    if city_filter:
        filtered_pincode_data = filtered_pincode_data[filtered_pincode_data['city'].isin(city_filter)]
    unique_pincodes = sorted({
        p.strip()
        for sublist in filtered_pincode_data['pincode'].str.split(',')
        for p in sublist if p.strip()
    })
    return st.sidebar.multiselect(
        "Select Pincode",
        options=unique_pincodes,
        key="pincode_filter"
    )

def get_speciality_filter(medical_data, pincode_filter):
    filtered_speciality_data = medical_data.copy()
    if pincode_filter:
        filtered_speciality_data = filtered_speciality_data[
            filtered_speciality_data['pincode'].str.split(',').apply(
                lambda x: any(p in pincode_filter for p in x)
            )
        ]
    unique_specialities = filtered_speciality_data['speciality'].dropna().unique()
    return st.sidebar.multiselect(
        "Select Speciality",
        options=unique_specialities,
        key="speciality_filter"
    )
def main():
    # Set page configuration\
    medical_file = 'https://wondrx-internal.s3.ap-south-1.amazonaws.com/projects/dashboard/2-jan-wondrxprod_wondrx_diitized_data_with_drug.xlsx'
    st.set_page_config(layout="wide", page_title="Dashboard")

    col1, col2 = st.columns([5, 1])
    with col1:
        title_placeholder = st.empty()
    with col2:
        logo_path = 'logo.png'
        st.image(logo_path, width=150)

    
    # Load datasets
    
    medical_data = load_data(medical_file)

    # Sidebar filters for patient data
    # Sidebar filters for patient data
    st.sidebar.title("Rx Analytics Filters")

    # State filter
    state_filter = get_state_filter(medical_data)
    city_filter = get_city_filter(medical_data, state_filter)
    pincode_filter = get_pincode_filter(medical_data, state_filter, city_filter)
    speciality_filter = get_speciality_filter(medical_data, pincode_filter)

    st.sidebar.header("Analytics Time Period")
    # First row of buttons
    col1, col2 = st.sidebar.columns(2)
    start_date_val = datetime(2020, 1, 1)
    end_date_val = datetime.today()
    
    if col1.button("Current FY"):
        current_year = datetime.today().year
        start_date_val = datetime(current_year - 1, 4, 1)
        end_date_val = datetime.today()
    if col2.button("Previous Month"):
        today = datetime.today()
        first_day_current_month = datetime(today.year, today.month, 1)
        last_day_prev_month = first_day_current_month - pd.Timedelta(days=1)
        start_date_val = datetime(last_day_prev_month.year, last_day_prev_month.month, 1)
        end_date_val = last_day_prev_month

    # Second row of buttons
    col3, col4 = st.sidebar.columns([1,1])
    if col3.button("Year To Date"):
        today = datetime.today()
        start_date_val = datetime(today.year, 1, 1)
        end_date_val = today
    if col4.button("Previous Week"):
        today = datetime.today()
        start_date_val = today - pd.Timedelta(days=today.weekday() + 7)
        end_date_val = start_date_val + pd.Timedelta(days=6)
    
    
    start_date = st.sidebar.date_input(
        "Start Date",
        value=start_date_val,
        key="start_date",
        max_value=datetime.today(),
        format="DD-MM-YYYY",
    )
    end_date = st.sidebar.date_input(
        "End Date",
        value=end_date_val,
        key="end_date",
        min_value=start_date,
        max_value=datetime.today(),
        format="DD-MM-YYYY",
    )
    title_placeholder.title(f"From: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}")

    filtered_medical_data = filter_by_date_range(
        clean_medical_data(
            apply_filters(
                medical_data,
                state_filter,
                city_filter,
                pincode_filter,
                speciality_filter
            )
        ),
        start_date,
        end_date
    )

    if filtered_medical_data.empty:
        st.warning("No data available.")
        return


    # Visualization Tabs
    tab1, tab2, tab3, tab4,tab5,tab6,tab7,tab8,tab9,tab10,tab11  = st.tabs([
        "🏷️ Manufacturer Analysis",
        "📂 Data Types within Rx",
        "📍 Geographical Distribution",
        "📊 Demographic Distribution",
        "💊 Medicines",
        "🏭 Pharma Analytics",
        "🩺 Observations",
        "🧪 Diagnostics",
        "🔍 Manufacturer Comparison",
        "💰 Value-Based Comparison",
        "🏭 Market Share by primary use"
    ])
    display_sidebar_totals(filtered_medical_data)


    # Visualizations for each tab
    visualize_manufacturer_medicines(tab1, filtered_medical_data)
    visualize_data_types(tab2, filtered_medical_data)
    visualize_geographical_distribution(tab3, filtered_medical_data)
    visualize_patient_demographics(tab4, filtered_medical_data)
    visualize_medicines(tab5, filtered_medical_data)
    visualize_pharma_analytics(tab6, filtered_medical_data)
    visualize_observations(tab7, filtered_medical_data)
    visualize_diagnostics(tab8, filtered_medical_data)
    manufacturer_comparison_tab(tab9, filtered_medical_data)
    visualize_value_comparison(tab10, filtered_medical_data)
    visualize_market_share_primary_use(tab11, filtered_medical_data)

if __name__ == "__main__":
    main()

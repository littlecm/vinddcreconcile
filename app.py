import streamlit as st
import pandas as pd
import requests

# Function to download CSV from URL
def download_csv(url):
    response = requests.get(url)
    if response.ok:
        return pd.read_csv(pd.compat.StringIO(response.text))
    return pd.DataFrame()

# Function to reconcile VINs between two datasets
def reconcile_vins(vinsolutions_data, coxautomotive_data, vehicle_type_column, filter_value):
    # Filter datasets based on vehicle type and filter value
    vinsolutions_filtered = vinsolutions_data[vinsolutions_data[vehicle_type_column] == filter_value]
    coxautomotive_filtered = coxautomotive_data[coxautomotive_data['type'] == filter_value]

    # Identify common and unique VINs
    common_vins = set(vinsolutions_filtered['VIN']).intersection(set(coxautomotive_filtered['vin']))
    unique_vinsolutions_vins = set(vinsolutions_filtered['VIN']) - set(coxautomotive_filtered['vin'])
    unique_coxautomotive_vins = set(coxautomotive_filtered['vin']) - set(vinsolutions_filtered['VIN'])

    results = [{'VIN': vin, 'Result': "Appearing in both datasets"} for vin in common_vins]
    results.extend([{'VIN': vin, 'Result': "Unique to VINsolutions"} for vin in unique_vinsolutions_vins])
    results.extend([{'VIN': vin, 'Result': "Unique to Dealer.com"} for vin in unique_coxautomotive_vins])
    
    return results

def main():
    st.title('VIN Reconciliation Tool')

    # Input for specifying the CSV filename
    vinsolutions_filename = st.text_input("Enter the VINsolutions CSV filename")
    vehicle_type_column = st.text_input("Column name for Vehicle Type", "Type")
    filter_value = st.text_input("Filter value for Vehicle Type (e.g., 'Used')", "Used")

    dealer_id_url = "https://feeds.amp.auto/feeds/coxautomotive/dealerdotcom.csv"
    dealers_df = download_csv(dealer_id_url)
    dealer_id = st.selectbox("Select Dealer ID", options=dealers_df['dealer_id'].unique() if not dealers_df.empty else [])

    if st.button('Reconcile Data'):
        vinsolutions_url = f"https://feeds.amp.auto/feeds/vinsolutions/{vinsolutions_filename}"
        vinsolutions_data = download_csv(vinsolutions_url)
        coxautomotive_data = download_csv(dealer_id_url)

        if not vinsolutions_data.empty and not coxautomotive_data.empty:
            results = reconcile_vins(vinsolutions_data, coxautomotive_data, vehicle_type_column, filter_value)
            results_df = pd.DataFrame(results)
            st.write("Reconciliation Results:", results_df)
        else:
            st.error("Error loading data. Please check the filenames and internet connection.")

if __name__ == "__main__":
    main()

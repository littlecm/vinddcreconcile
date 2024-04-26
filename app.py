import streamlit as st
import pandas as pd
import requests

# Function to download CSV data from URL
def download_csv(url):
    response = requests.get(url)
    if response.ok:
        return pd.read_csv(pd.compat.StringIO(response.text))
    else:
        st.error('Failed to download data.')
        return pd.DataFrame()

# Function to perform reconciliation and additional checks
import requests
import pandas as pd

def reconcile_vins(vinsolutions_data, coxautomotive_data):
    # Intersect and unique sets
    common_vins = set(vinsolutions_data['VIN']).intersection(set(coxautomotive_data['vin']))
    unique_vinsolutions_vins = set(vinsolutions_data['VIN']) - set(coxautomotive_data['vin'])
    unique_coxautomotive_vins = set(coxautomotive_data['vin']) - set(vinsolutions_data['VIN'])

    # Prepare headers for the API call
    headers = {
        "authority": "cws.gm.com",
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # List to hold the results
    results = []

    # Handle common VINs
    for vin in common_vins:
        results.append({'VIN': vin, 'Result': "Appearing"})

    # Handle unique VINs from both datasets
    for vin in unique_coxautomotive_vins.union(unique_vinsolutions_vins):
        api_url = f"https://cws.gm.com/vs-cws/vehshop/v2/vehicle?vin={vin}&postalCode=48640&locale=en_US"
        api_response = requests.get(api_url, headers=headers)

        if api_response.ok:
            api_data = api_response.json()

            # Check for recall information first
            if "recallInfo" in api_data and "This vehicle is temporarily unavailable" in api_data["recallInfo"]:
                results.append({'VIN': vin, 'Result': "Vehicle with Recall"})
                continue  # Skip to next VIN as recall information takes precedence

            # Then check for inventory status
            if "inventoryStatus" in api_data:
                inventory_status = api_data["inventoryStatus"].get("name")
                if inventory_status:
                    if inventory_status == "In Transit":
                        result_label = "In Transit - Not expected in HomeNet" if vin in unique_coxautomotive_vins else "Exclusive to VINsolutions"
                    else:
                        result_label = f"Other Inventory Status: {inventory_status}"
                else:
                    result_label = "Exclusive" if vin in unique_coxautomotive_vins else "Exclusive to VINsolutions"
            else:
                result_label = "API request failed - Status not found"
        else:
            result_label = "API request failed"

        results.append({'VIN': vin, 'Result': result_label})

    return results

def main():
    st.title('VIN Reconciliation Tool')

    # User inputs
    vinsolutions_filename = st.text_input("Enter the VINsolutions CSV filename (e.g., 'dealer-12345.csv')")
    dealer_id = st.text_input("Enter dealer ID (e.g., 'garberchevroletofsaginawgm')")

    if vinsolutions_filename and dealer_id:
        # Download and parse VINsolutions CSV
        vinsolutions_url = f"https://feeds.amp.auto/feeds/vinsolutions/{vinsolutions_filename}"
        vinsolutions_data = download_csv(vinsolutions_url)
        
        # Filter VINsolutions data for "Used" vehicles if needed
        vinsolutions_data_used = vinsolutions_data[vinsolutions_data['Type'] == 'Used']

        # Download and parse Dealer.com CSV
        dealerdotcom_url = "https://feeds.amp.auto/feeds/coxautomotive/dealerdotcom.csv"
        coxautomotive_data = download_csv(dealerdotcom_url)
        
        # Filter Dealer.com data for "Used" vehicles and specific dealer_id
        coxautomotive_data_used = coxautomotive_data[(coxautomotive_data['type'] == 'Used') & (coxautomotive_data['dealer_id'] == dealer_id)]

        # Reconcile VINs
        results = reconcile_vins(vinsolutions_data_used, coxautomotive_data_used)

        # Display results
        results_df = pd.DataFrame(results)
        st.write("Reconciliation Results:", results_df)

if __name__ == "__main__":
    main()

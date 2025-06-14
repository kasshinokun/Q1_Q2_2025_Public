import streamlit as st
import pandas as pd
import json
import requests
from io import StringIO

st.title("CSV Column Unique Values Extractor")
st.markdown("""
This app reads a CSV file from a GitHub URL, extracts unique values for each column,
and allows you to download the results as JSON.
""")

st.write("GitHub URL: https://github.com/kasshinokun/Q1_Q2_2025_Public/raw/main/Aulas_AED3/TP_AED_E3/data/traffic_accidents_rev2.csv")
# GitHub URL input
github_url = "https://github.com/kasshinokun/Q1_Q2_2025_Public/raw/main/Aulas_AED3/TP_AED_E3/data/traffic_accidents_rev2.csv"



#https://github.com/kasshinokun/Q1_Q2_2025_Public/blob/main/Aulas_AED3/TP_AED_E3/data/traffic_accidents_pt_br_rev2.csv
if github_url:
    try:
        # Fetch CSV data
        response = requests.get(github_url,stream=True)
        response.raise_for_status()
        
        # Load data into DataFrame
        #df = pd.read_csv(StringIO(response.text))
        df = pd.read_csv(StringIO(response.text), encoding='latin-1', sep=';')
        st.success("CSV loaded successfully!")
        
        # Display preview
        st.subheader("Data Preview")
        st.dataframe(df.head())

        # Extract unique values
        unique_values = {}
        for column in df.columns:
            unique_values[column] = df[column].unique().tolist()
        
        # Convert to JSON
        json_data = json.dumps(unique_values, indent=4)
        
        # Show JSON preview
        st.subheader("Unique Values Preview")
        st.json(unique_values)
        
        # Download button
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name="unique_values.json",
            mime="application/json"
        )
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
    except pd.errors.ParserError:
        st.error("Error parsing CSV file. Please check the URL points to a valid CSV.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
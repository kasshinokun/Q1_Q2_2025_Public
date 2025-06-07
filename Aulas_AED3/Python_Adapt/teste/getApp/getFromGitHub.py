import streamlit as st
import pandas as pd
import os
from pathlib import Path

import shutil
import io
import requests


def main():
    st.title("CSV Data Processor")

    # URL of the CSV file
    csv_url = "https://github.com/kasshinokun/Q1_Q2_2025_Public/raw/main/Aulas_AED3/TP_AED_E3/data/traffic_accidents_pt_br_rev2.csv"
    documents_path = Path.home() / 'Documents'/'traffic_accidents_pt_br_rev2.csv'
    try:
        #s = requests.get(csv_url).content
        response  = requests.get(csv_url, stream=True)
        # Load the CSV file into a pandas DataFrame with 'latin-1' encoding and semicolon separator
        #df = pd.read_csv(io.StringIO(s.decode('latin-1')))
        st.success("CSV file loaded successfully!")
        with open(documents_path, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
            st.success('The CSV file was saved successfully')

            # Load the CSV file into a pandas DataFrame with 'latin-1' encoding and semicolon separator
            df = pd.read_csv(documents_path, encoding='latin-1', sep=';')
            #df = pd.read_csv(csv_url)
            st.success("CSV file loaded on Pandas Dataframe successfully!")
            st.dataframe(df)

            # Create headerCSV list
            headerCSV = list(df.columns)

            st.write(headerCSV)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")



if __name__ == "__main__":    
    main()

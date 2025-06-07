import streamlit as st
import pandas as pd
import os
from pathlib import Path

def main():
    st.title("CSV Data Processor")
    
    # URL of the CSV file
    csv_url = "https://github.com/kasshinokun/Q1_Q2_2025_Public/raw/main/Aulas_AED3/TP_AED_E3/data/traffic_accidents_pt_br_rev2.csv"
    
    try:
        # Load the CSV file into a pandas DataFrame
        df = pd.read_csv(csv_url)
        
        st.success("CSV file loaded successfully!")
        st.write(f"Data shape: {df.shape}")
        
        # Create headerCSV list
        headerCSV = list(df.columns)
        
        # Create dataCSV list of lists with proper data types
        dataCSV = []
        for _, row in df.iterrows():
            row_data = []
            
            # Columns 0 to 13 and 15 as strings
            for i in range(14):
                row_data.append(str(row[i]) if pd.notna(row[i]) else "")
            row_data.append(str(row[15]) if pd.notna(row[15]) else "")
            
            # Columns 16 to 21 as floats
            for i in range(16, 22):
                row_data.append(float(row[i]) if pd.notna(row[i]) else 0.0)
            
            # Column 14 and 22 to 24 as ints
            row_data.append(int(row[14]) if pd.notna(row[14]) else 0)
            for i in range(22, 25):
                row_data.append(int(row[i]) if pd.notna(row[i]) else 0)
            
            dataCSV.append(row_data)
        
        # Get the documents folder path
        documents_path = Path.home() / "Documents"
        output_file = documents_path / "data.py"
        
        # Write to data.py file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("headerCSV = [\n")
            for header in headerCSV:
                f.write(f'    "{header}",\n')
            f.write("]\n\n")
            
            f.write("dataCSV = [\n")
            for row in dataCSV:
                f.write("    [\n")
                for i, value in enumerate(row):
                    if i < 14 or i == 15:  # String columns
                        f.write(f'        "{value}",\n')
                    elif 16 <= i <= 21:  # Float columns
                        f.write(f'        {float(value)},\n')
                    else:  # Int columns
                        f.write(f'        {int(value)},\n')
                f.write("    ],\n")
            f.write("]\n")
        
        st.success(f"File 'data.py' successfully written to {documents_path}")
        
        # Show a preview of the data
        if st.checkbox("Show data preview"):
            st.write(df.head())
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
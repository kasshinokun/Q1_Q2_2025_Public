import streamlit as st
import pandas as pd
import json
import requests
from io import BytesIO

class CSVUniqueValuesExtractor:
    def __init__(self):
        self.github_url = ""
        self.encoding = "utf-8"
        self.df = None
        self.unique_values = {}
        self.json_data = ""
        
    def set_github_url(self, url):
        self.github_url = url
        
    def set_encoding(self, encoding):
        self.encoding = encoding
        
    def fetch_csv(self):
        """Fetch CSV content from GitHub URL with streaming"""
        with requests.get(self.github_url, stream=True) as response:
            response.raise_for_status()
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
            return BytesIO(content)
    
    def load_dataframe(self, content):
        """Load CSV content into pandas DataFrame"""
        self.df = pd.read_csv(content, encoding=self.encoding)
        
    def compute_unique_values(self):
        """Compute unique values for each column"""
        self.unique_values = {}
        for column in self.df.columns:
            self.unique_values[column] = self.df[column].dropna().unique().tolist()
        
    def generate_json(self):
        """Generate JSON from unique values"""
        self.json_data = json.dumps(self.unique_values, indent=4)
        
    def display_preview(self):
        """Display DataFrame and JSON previews"""
        st.subheader("Data Preview")
        st.dataframe(self.df.head())
        
        st.subheader("Unique Values Preview")
        st.json(self.unique_values)
        
    def download_json(self):
        """Create JSON download button"""
        st.download_button(
            label="Download JSON",
            data=self.json_data,
            file_name="unique_values.json",
            mime="application/json"
        )
        
    def run(self):
        """Main application flow"""
        st.title("CSV Column Unique Values Extractor")
        st.markdown("""
        This app reads a CSV file from a GitHub URL, extracts unique values for each column,
        and allows you to download the results as JSON.
        """)
        
        # User inputs
        self.set_github_url(st.text_input(
            "Enter GitHub CSV URL (raw content):",
            placeholder="https://raw.githubusercontent.com/.../file.csv"
        ))
        
        self.set_encoding(st.selectbox(
            "Select file encoding:",
            options=['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16'],
            index=0,
            help="Select the character encoding of the CSV file"
        ))
        
        if self.github_url:
            try:
                # Fetch and process CSV
                content = self.fetch_csv()
                self.load_dataframe(content)
                st.success(f"CSV loaded successfully with {self.encoding} encoding!")
                
                # Compute and display results
                self.compute_unique_values()
                self.generate_json()
                self.display_preview()
                self.download_json()
                
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching data: {e}")
            except pd.errors.EmptyDataError:
                st.error("The CSV file is empty.")
            except UnicodeDecodeError:
                st.error(f"Decoding error with {self.encoding} encoding. Try a different encoding.")
            except pd.errors.ParserError:
                st.error("Error parsing CSV file. Please check the file format.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# Run the application
if __name__ == "__main__":
    app = CSVUniqueValuesExtractor()
    app.run()
import streamlit as st
import pandas as pd
import json
import requests
from io import BytesIO
import time
import re
from deep_translator import GoogleTranslator

class CSVUniqueValuesExtractor:
    def __init__(self):
        self.github_url = ""
        self.encoding = "utf-8"
        self.df = None
        self.unique_values = {}
        self.translated_values = {}
        self.json_data = ""
        self.translate_enabled = False
        
    def set_github_url(self, url):
        self.github_url = url
        
    def set_encoding(self, encoding):
        self.encoding = encoding
        
    def set_translate_enabled(self, enabled):
        self.translate_enabled = enabled
        
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
    
    def clean_text(self, text):
        """Clean text for better translation"""
        # Remove special characters except spaces and basic punctuation
        cleaned = re.sub(r'[^\w\s.,;:?!-]', '', str(text))
        # Remove extra whitespace
        return re.sub(r'\s+', ' ', cleaned).strip()
    
    def translate_values(self):
        """Translate unique values from English to Brazilian Portuguese"""
        self.translated_values = {}
        total_values = sum(len(values) for values in self.unique_values.values())
        if total_values == 0:
            return
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        processed_count = 0
        
        try:
            translator = GoogleTranslator(source='en', target='pt')
            
            for column, values in self.unique_values.items():
                self.translated_values[column] = []
                for val in values:
                    # Only translate string values
                    if isinstance(val, str):
                        cleaned_val = self.clean_text(val)
                        if cleaned_val:
                            try:
                                translated = translator.translate(cleaned_val)
                                self.translated_values[column].append(translated)
                            except Exception as e:
                                # Fallback to original on error
                                self.translated_values[column].append(val)
                                st.warning(f"Error translating '{val}': {str(e)}")
                        else:
                            self.translated_values[column].append(val)
                    else:
                        # Keep non-string values as-is
                        self.translated_values[column].append(val)
                    
                    # Update progress
                    processed_count += 1
                    progress = min(processed_count / total_values, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Translating: {processed_count}/{total_values} values")
                    
                    # Add delay to avoid rate limits
                    time.sleep(0.1)
        finally:
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
    
    def generate_json(self):
        """Generate JSON output structure"""
        if self.translate_enabled and self.translated_values:
            output = {
                "original": self.unique_values,
                "translated": self.translated_values
            }
        else:
            output = self.unique_values
        self.json_data = json.dumps(output, indent=4, ensure_ascii=False)
        
    def display_preview(self):
        """Display DataFrame and JSON previews"""
        st.subheader("Data Preview")
        st.dataframe(self.df.head())

        st.subheader("Unique Values Preview")
        if self.translate_enabled and self.translated_values:
            tab1, tab2 = st.tabs(["Original", "Translated"])
            with tab1:
                st.json(self.unique_values)
            with tab2:
                st.json(self.translated_values)
        else:
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
        st.title("📊 CSV Column Unique Values Extractor")
        st.markdown("""
        This app reads a CSV file from a GitHub URL, extracts unique values for each column,
        and allows you to download the results as JSON with optional translation to Brazilian Portuguese.
        """)
        
        # User inputs
        self.set_github_url(st.text_input(
            "Enter GitHub CSV URL (raw content):",
            placeholder="https://raw.githubusercontent.com/.../file.csv"
        ))
        
        col1, col2 = st.columns(2)
        with col1:
            self.set_encoding(st.selectbox(
                "Select file encoding:",
                options=['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16'],
                index=0,
                help="Select the character encoding of the CSV file"
            ))
        
        with col2:
            self.set_translate_enabled(st.checkbox(
                "Translate to Brazilian Portuguese",
                help="Enable to translate unique values from English to Portuguese"
            ))
        
        if self.github_url:
            try:
                # Fetch and process CSV
                content = self.fetch_csv()
                self.load_dataframe(content)
                st.success(f"✅ CSV loaded successfully with {self.encoding} encoding!")
                
                # Compute unique values
                self.compute_unique_values()
                
                # Translate if enabled
                if self.translate_enabled:
                    with st.spinner("Translating values. This may take a while..."):
                        self.translate_values()
                
                # Generate and display results
                self.generate_json()
                self.display_preview()
                self.download_json()
                
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error fetching data: {e}")
            except pd.errors.EmptyDataError:
                st.error("❌ The CSV file is empty.")
            except UnicodeDecodeError:
                st.error(f"❌ Decoding error with {self.encoding} encoding. Try a different encoding.")
            except pd.errors.ParserError:
                st.error("❌ Error parsing CSV file. Please check the file format.")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {e}")

# Run the application
if __name__ == "__main__":
    app = CSVUniqueValuesExtractor()
    app.run()
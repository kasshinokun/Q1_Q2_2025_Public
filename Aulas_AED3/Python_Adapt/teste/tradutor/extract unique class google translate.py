import streamlit as st
import pandas as pd
import json
import requests
from io import BytesIO
from googletrans import Translator, LANGUAGES # Import Translator and LANGUAGES from googletrans

class CSVUniqueValuesExtractor:
    def __init__(self):
        self.github_url = ""
        self.encoding = "utf-8"
        self.df = None
        self.unique_values = {}
        self.translated_unique_values = {} # New attribute for translated values
        self.json_data = ""
        self.translator = Translator() # Initialize the Googletrans Translator
        
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
    
    def translate_unique_values(self, target_language='en'):
        """Translate unique values for each column using googletrans"""
        self.translated_unique_values = {}
        for column, values in self.unique_values.items():
            translated_list = []
            for item in values:
                if isinstance(item, str) and item.strip() != "": # Only translate non-empty strings
                    try:
                        translated_text = self.translator.translate(item, dest=target_language).text
                        translated_list.append(translated_text)
                    except Exception as e:
                        translated_list.append(f"Translation Error: {e}")
                        st.warning(f"Could not translate '{item}': {e}")
                else:
                    translated_list.append(item) # Keep non-string or empty values as they are
            self.translated_unique_values[column] = translated_list
            
    def generate_json(self, use_translated=False):
        """Generate JSON from unique values, optionally using translated values"""
        if use_translated:
            self.json_data = json.dumps(self.translated_unique_values, indent=4, ensure_ascii=False)
        else:
            self.json_data = json.dumps(self.unique_values, indent=4, ensure_ascii=False)
        
    def display_preview(self, use_translated=False):
        """Display DataFrame and JSON previews"""
        st.subheader("Data Preview")
        st.dataframe(self.df.head())
        
        st.subheader("Unique Values Preview")
        if use_translated:
            st.json(self.translated_unique_values)
        else:
            st.json(self.unique_values)
        
    def download_json(self, use_translated=False):
        """Create JSON download button"""
        file_name = "unique_values.json"
        if use_translated:
            file_name = f"unique_values_translated_{st.session_state.target_lang}.json" # Add language to filename
        
        st.download_button(
            label="Download JSON",
            data=self.json_data,
            file_name=file_name,
            mime="application/json"
        )
        
    def run(self):
        """Main application flow"""
        st.title("CSV Column Unique Values Extractor")
        st.markdown("""
        This app reads a CSV file from a GitHub URL, extracts unique values for each column,
        and allows you to download the results as JSON. It can also translate the unique values.
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

        st.subheader("Translation Options")
        enable_translation = st.checkbox("Enable Translation")
        
        if enable_translation:
            # Create a mapping from language name to language code for the selectbox
            lang_options = {name: code for code, name in LANGUAGES.items()}
            selected_lang_name = st.selectbox(
                "Select Target Language for Translation:",
                options=list(lang_options.keys()),
                index=list(lang_options.keys()).index('english') # Default to English
            )
            # Store the selected language code in session state
            st.session_state.target_lang = lang_options[selected_lang_name]
        
        if self.github_url:
            try:
                # Fetch and process CSV
                content = self.fetch_csv()
                self.load_dataframe(content)
                st.success(f"CSV loaded successfully with {self.encoding} encoding!")
                
                # Compute and display results
                self.compute_unique_values()
                
                if enable_translation and st.session_state.target_lang:
                    with st.spinner(f"Translating to {st.session_state.target_lang}... This may take a moment."):
                        self.translate_unique_values(st.session_state.target_lang)
                    self.generate_json(use_translated=True)
                    self.display_preview(use_translated=True)
                    self.download_json(use_translated=True)
                    st.info("Note: Googletrans relies on Google Translate's unofficial API and might be rate-limited or unstable with frequent use.")
                else:
                    self.generate_json(use_translated=False)
                    self.display_preview(use_translated=False)
                    self.download_json(use_translated=False)
                
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
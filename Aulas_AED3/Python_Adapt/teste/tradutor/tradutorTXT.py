from googletrans import Translator
import streamlit as st
import pandas as pd

translator = Translator()

# Função para traduzir texto usando googletrans
def translate(s):
    return translator.translate(s, dest="pt").text

# Função para ler e enviar a tradução
def translate_text():
    with open('traffic_accidents_rev2.csv', "r") as infile, open('traffic_accidents_pt_rev2.csv', "w") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for row in reader:
            translated_row = [translate(item) for item in row]
            writer.writerow(translated_row)
        return outfile
        
def main():
    st.title("CSV Data Translator")
    try:
        # Ler o arquivo original
        df.to_csv(translate_text(), sep=';', index=False, encoding='utf-8')
        st.success('The CSV file was tranlated successfully')

        # Load the CSV file into a pandas DataFrame with 'latin-1' encoding and semicolon separator
        
        #df = pd.read_csv(csv_url)
        st.success("CSV file loaded on Pandas Dataframe successfully!")
        st.dataframe(df)

        # Create headerCSV list
        headerCSV = list(df.columns)

        st.write(headerCSV)
    except Exception as f:
        st.error(f"An error occurred: {str(f)}")



if __name__ == "__main__":    
    main()


import csv
import json
from googletrans import Translator # You might need to install this: pip install googletrans==4.0.0-rc1
import os # For checking if a file exists
from pathlib import Path

def get_unique_csv_data(csv_filepath, column_index=0):
    """
    Reads a CSV file and extracts unique, non-empty strings from a specified column.

    Args:
        csv_filepath (str): The path to the input CSV file.
        column_index (int): The zero-based index of the column to extract data from.

    Returns:
        set: A set containing unique string items from the specified CSV column.
              Returns an empty set if the file is not found or an error occurs.
    """
    unique_items = set()
    print(f"Attempting to read unique data from CSV: '{csv_filepath}' (column index: {column_index})")
    try:
        with open(csv_filepath, 'r', newline='', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row_num, row in enumerate(csv_reader, 1):
                if not row: # Skip completely empty rows
                    continue
                
                # Check if the column index is valid for the current row
                if column_index >= len(row):
                    print(f"  Warning: Row {row_num} has fewer columns ({len(row)}) than specified index ({column_index}). Skipping data extraction for this row: {row}")
                    continue

                cell_content = row[column_index].strip() # Get content and remove leading/trailing whitespace
                if cell_content: # Only add non-empty strings to the set
                    unique_items.add(cell_content)
        print(f"Successfully extracted {len(unique_items)} unique items from '{csv_filepath}'.")
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_filepath}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred while reading CSV '{csv_filepath}': {e}")
    return unique_items

def perform_translation(items_to_translate, src_lang='en', dest_lang='pt'):
    """
    Translates a collection of text items using Google Translate.

    Args:
        items_to_translate (set or list): A collection of strings to translate.
        src_lang (str): The source language code (e.g., 'en').
        dest_lang (str): The destination language code (e.g., 'pt').

    Returns:
        dict: A dictionary where keys are original phrases and values are their translations.
              Includes error messages for failed translations.
    """
    translator = Translator() # Initialize translator once
    translated_data = {}
    total_items = len(items_to_translate)
    
    if total_items == 0:
        print("No items to translate.")
        return translated_data

    print(f"\nStarting translation of {total_items} unique items from '{src_lang}' to '{dest_lang}'...")

    # Convert set to sorted list for consistent iteration and progress display
    for i, item in enumerate(sorted(list(items_to_translate)), 1):
        try:
            translation = translator.translate(item, src=src_lang, dest=dest_lang)
            translated_data[item] = translation.text
            print(f"  [{i}/{total_items}] Translated: '{item}' -> '{translation.text}'")
        except Exception as e:
            print(f"  [{i}/{total_items}] Error translating '{item}': {e}")
            translated_data[item] = f"Translation_Error: {e}" # Store error message
    
    return translated_data

def save_dictionary_to_json(data_dict, json_filepath):
    """
    Saves a Python dictionary to a JSON file.

    Args:
        data_dict (dict): The dictionary to save.
        json_filepath (str): The path to the output JSON file.
    """
    print(f"Attempting to save translated data to JSON: '{json_filepath}'")
    try:
        # Use ensure_ascii=False to correctly handle non-ASCII characters (e.g., Portuguese accents)
        # indent=4 makes the JSON file human-readable
        with open(json_filepath, 'w', encoding='utf-8') as json_file:
            json.dump(data_dict, json_file, indent=4, ensure_ascii=False)
        print(f"Successfully saved translation dictionary to '{json_filepath}'.")
    except IOError as e:
        print(f"Error: Could not write JSON file '{json_filepath}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving JSON: {e}")

def main():
    """
    Main function to orchestrate the CSV reading, translation, and JSON writing process.
    """
    print("--- Unified CSV to Translated JSON Script ---")

    # --- Configuration ---
    # Define your input CSV file, output JSON file, and relevant settings here
    csv_input_file = os.path.join(Path.home(), 'Documents', 'Data','traffic_accidents_rev2.csv')
    json_output_file = os.path.join(Path.home(), 'Documents', 'Data','translated_output.json')
    csv_column_to_read = 0  # 0 for the first column, 1 for the second, etc.
    source_language = 'en'  # Source language code (e.g., 'en', 'pt', 'es')
    destination_language = 'pt' # Destination language code (e.g., 'pt', 'en', 'fr')
    # --- End Configuration ---

    # 1. Create a dummy CSV file if it doesn't exist for easy testing
    if not os.path.exists(csv_input_file):
        print(f"'{csv_input_file}' not found. Creating a dummy CSV file for demonstration.")
        dummy_csv_content = [
            ['Hello World', 'Greeting'],
            ['Python programming', 'Technology'],
            ['OpenAI API', 'AI'],
            ['Hello World', 'Duplicate for uniqueness test'],
            ['How are you?', 'Question'],
            ['   Spaces and Tabs   ', 'Whitespace test'], # Example with leading/trailing spaces
            ['', 'Empty cell test'], # Example of an empty cell
            ['Another Phrase'] # Example of a row with fewer columns
        ]
        try:
            with open(csv_input_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(dummy_csv_content)
            print(f"Dummy '{csv_input_file}' created.")
        except Exception as e:
            print(f"Error creating dummy CSV: {e}")
            return # Exit if we can't even create the dummy file

    # 2. Get unique items from the CSV file
    unique_phrases = get_unique_csv_data(csv_input_file, csv_column_to_read)

    if not unique_phrases:
        print("No unique phrases were extracted from the CSV. Exiting.")
        return

    # 3. Perform translation of the unique items
    translations = perform_translation(unique_phrases, source_language, destination_language)

    if not translations:
        print("No translations were successfully performed. Exiting.")
        return

    # 4. Save the translations dictionary to a JSON file
    save_dictionary_to_json(translations, json_output_file)

    print("\n--- Script Finished ---")

if __name__ == "__main__":
    main()

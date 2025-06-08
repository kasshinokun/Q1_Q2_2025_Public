import csv
import json
from googletrans import Translator
import os

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
    print(f"-> Reading unique data from CSV: '{csv_filepath}' (column index: {column_index})")
    try:
        with open(csv_filepath, 'r', newline='', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row_num, row in enumerate(csv_reader, 1):
                if not row: # Skip completely empty rows
                    continue

                if column_index >= len(row):
                    print(f"  Warning: Row {row_num} has fewer columns ({len(row)}) than specified index ({column_index}). Skipping cell extraction for this row: {row}")
                    continue

                cell_content = row[column_index].strip() # Get content and remove whitespace
                if cell_content: # Only add non-empty strings to the set
                    unique_items.add(cell_content)
        print(f"<- Successfully extracted {len(unique_items)} unique items from '{csv_filepath}'.")
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
        print("-> No items to translate.")
        return translated_data

    print(f"\n-> Starting translation of {total_items} unique items from '{src_lang}' to '{dest_lang}'...")

    # Convert set to sorted list for consistent iteration and progress display
    for i, item in enumerate(sorted(list(items_to_translate)), 1):
        try:
            translation = translator.translate(item, src=src_lang, dest=dest_lang)
            translated_data[item] = translation.text
            print(f"  [{i}/{total_items}] Translated: '{item}' -> '{translation.text}'")
        except Exception as e:
            print(f"  [{i}/{total_items}] Error translating '{item}': {e}")
            translated_data[item] = f"Translation_Error: {e}" # Store error message

    print(f"<- Finished translating {len(translated_data)} items.")
    return translated_data

def save_dictionary_to_json(data_dict, json_filepath):
    """
    Saves a Python dictionary to a JSON file.

    Args:
        data_dict (dict): The dictionary to save.
        json_filepath (str): The path to the output JSON file.
    """
    print(f"\n-> Saving translated data to JSON: '{json_filepath}'")
    try:
        # Use ensure_ascii=False to correctly handle non-ASCII characters (e.g., Portuguese accents)
        # indent=4 makes the JSON file human-readable
        with open(json_filepath, 'w', encoding='utf-8') as json_file:
            json.dump(data_dict, json_file, indent=4, ensure_ascii=False)
        print(f"<- Successfully saved translation dictionary to '{json_filepath}'.")
    except IOError as e:
        print(f"Error: Could not write JSON file '{json_filepath}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while saving JSON: {e}")

def rewrite_csv_with_dictionary_values(
    input_csv_filepath,
    output_csv_filepath,
    mapping_dictionary, # This will be the translation dictionary
    case_sensitive_replace=False
):
    """
    Reads a CSV file, replaces cell content if it's a key in the mapping dictionary,
    and writes the modified data to a new CSV file.

    Args:
        input_csv_filepath (str): The path to the input CSV file.
        output_csv_filepath (str): The path where the modified CSV file will be saved.
        mapping_dictionary (dict): A dictionary where keys are original cell contents
                                   and values are the replacements.
        case_sensitive_replace (bool): If True, dictionary key matching is case-sensitive.
                                       If False, both cell content and dictionary keys are
                                       converted to lowercase for comparison.
    """
    modified_rows = []

    print(f"\n-> Starting CSV content replacement for '{input_csv_filepath}'")
    print(f"   Writing modified data to: '{output_csv_filepath}'")
    print(f"   Replacement will be case-sensitive: {case_sensitive_replace}")

    # Prepare a lowercase version of the mapping dictionary for efficient case-insensitive lookup
    normalized_mapping_dict = {k.lower(): v for k, v in mapping_dictionary.items()} if not case_sensitive_replace else mapping_dictionary


    try:
        with open(input_csv_filepath, 'r', newline='', encoding='utf-8') as infile:
            csv_reader = csv.reader(infile)

            for row_num, row in enumerate(csv_reader, 1):
                new_row = []
                for cell_num, cell_content in enumerate(row):
                    processed_cell_content = cell_content.strip() # Remove whitespace

                    lookup_key = processed_cell_content
                    if not case_sensitive_replace:
                        lookup_key = processed_cell_content.lower()

                    # Check if the lookup_key exists in our (potentially normalized) mapping dictionary
                    if lookup_key in normalized_mapping_dict:
                        replacement_value = normalized_mapping_dict[lookup_key]
                        new_row.append(replacement_value)
                        # print(f"  Row {row_num}, Cell {cell_num+1}: Replaced '{cell_content}' with '{replacement_value}'")
                    else:
                        new_row.append(cell_content) # Keep original content
                modified_rows.append(new_row)

        with open(output_csv_filepath, 'w', newline='', encoding='utf-8') as outfile:
            csv_writer = csv.writer(outfile)
            csv_writer.writerows(modified_rows)

        print(f"<- Successfully saved modified CSV data to '{output_csv_filepath}'.")

    except FileNotFoundError:
        print(f"Error: The input CSV file '{input_csv_filepath}' for replacement was not found.")
    except Exception as e:
        print(f"An unexpected error occurred during CSV replacement: {e}")

# --- Main execution part ---
def main():
    """
    Main function to orchestrate the entire process:
    1. Extract unique data from CSV.
    2. Translate unique data.
    3. Save translations to JSON.
    4. Replace original CSV content with translations.
    5. Save modified CSV.
    """
    print("--- Unified CSV Processing and Translation Script ---")

    # --- Configuration ---
    # Define your input CSV file, output JSON file, and relevant settings here
    INPUT_CSV_FILE = 'my_data.csv'
    OUTPUT_JSON_FILE = 'my_translations.json'
    OUTPUT_MODIFIED_CSV_FILE = 'my_data_translated.csv'

    CSV_COLUMN_TO_EXTRACT_FOR_TRANSLATION = 0  # 0 for the first column, 1 for the second, etc.
    SOURCE_LANGUAGE = 'en'  # Source language code (e.g., 'en', 'pt', 'es')
    DESTINATION_LANGUAGE = 'pt' # Destination language code (e.g., 'pt', 'en', 'fr')

    # Set to True if replacement should be case-sensitive (e.g., 'Apple' != 'apple')
    # If False, 'Apple' will match 'apple' in the translation dictionary if the key is 'apple'.
    REPLACEMENT_CASE_SENSITIVE = False
    # --- End Configuration ---

    # 1. Create a dummy CSV file if it doesn't exist for easy testing
    if not os.path.exists(INPUT_CSV_FILE):
        print(f"\n'{INPUT_CSV_FILE}' not found. Creating a dummy CSV file for demonstration.")
        dummy_data = [
            ['Product', 'Category', 'Color'],
            ['Apple', 'Fruit', 'Red'],
            ['Banana', 'Fruit', 'Yellow'],
            ['Computer', 'Electronic', 'Gray'],
            ['Orange', 'Fruit', 'orange'], # Example: lowercase 'orange'
            ['TEST', 'Other', ''], # Example: uppercase 'TEST'
            ['Hello', 'Greeting', 'World'],
            ['Spain', 'Country', 'Red'],
            ['Cat', 'Animal', 'Black'],
            ['Dog', 'Animal', 'Brown'],
            ['True', 'Boolean', 'False']
        ]
        try:
            with open(INPUT_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(dummy_data)
            print(f"Dummy '{INPUT_CSV_FILE}' created.")
        except Exception as e:
            print(f"Error creating dummy CSV: {e}")
            return # Exit if we can't create the dummy file

    # --- Step 1: Extract Unique Items from CSV ---
    unique_phrases_from_csv = get_unique_csv_data(
        INPUT_CSV_FILE,
        CSV_COLUMN_TO_EXTRACT_FOR_TRANSLATION
    )

    if not unique_phrases_from_csv:
        print("No unique phrases were extracted from the CSV for translation. Exiting.")
        return

    # --- Step 2: Perform Translation ---
    # Use only the items from the CSV that are relevant for translation
    translations_map = perform_translation(
        unique_phrases_from_csv,
        SOURCE_LANGUAGE,
        DESTINATION_LANGUAGE
    )

    if not translations_map:
        print("No translations were successfully performed. Exiting.")
        return

    # --- Step 3: Save Translations to JSON ---
    save_dictionary_to_json(translations_map, OUTPUT_JSON_FILE)

    # --- Step 4 & 5: Replace Content in Original CSV and Save Modified CSV ---
    # Use the `translations_map` as the dictionary for replacement
    rewrite_csv_with_dictionary_values(
        INPUT_CSV_FILE,
        OUTPUT_MODIFIED_CSV_FILE,
        translations_map, # This dictionary now contains original -> translated mappings
        case_sensitive_replace=REPLACEMENT_CASE_SENSITIVE
    )

    print("\n--- Script Finished ---")

if __name__ == "__main__":
    main()

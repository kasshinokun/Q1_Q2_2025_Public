import csv
import time
import os
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TextTooLong, RequestError

def translate_csv(input_path, output_path):
    """
    Translates each cell of a CSV file to Brazilian Portuguese and writes to a new CSV file.
    Handles rate limits, long text, and preserves CSV structure.
    """
    # Initialize translator
    translator = GoogleTranslator(source='auto', target='pt')
    
    # Track progress
    total_rows = 0
    translated_cells = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        for row in reader:
            total_rows += 1
            translated_row = []
            
            for cell in row:
                if not cell.strip():  # Skip empty cells
                    translated_row.append(cell)
                    continue
                
                try:
                    # Translate and add to new row
                    translated_cell = translator.translate(cell)
                    translated_row.append(translated_cell)
                    translated_cells += 1
                    
                    # Rate limiting: 1 request/second
                    time.sleep(1)
                    
                except TextTooLong:
                    # Handle text exceeding 5000 characters
                    print(f"⚠️ Cell too long ({len(cell)} chars) at row {total_rows}. Keeping original.")
                    translated_row.append(cell)
                except RequestError as e:
                    # Handle API request errors
                    print(f"🚨 Translation error: {e}. Keeping original text.")
                    translated_row.append(cell)
                    time.sleep(5)  # Longer wait after errors
                except Exception as e:
                    # Generic error handling
                    print(f"❌ Unexpected error: {e}. Keeping original text.")
                    translated_row.append(cell)
            
            writer.writerow(translated_row)
            
            # Print progress every 10 rows
            if total_rows % 10 == 0:
                print(f"📊 Processed {total_rows} rows ({translated_cells} cells translated)")

    print(f"\n✅ Translation complete!")
    print(f"   Total rows processed: {total_rows}")
    print(f"   Total cells translated: {translated_cells}")
    print(f"   Output file: {output_path}")

if __name__ == "__main__":
    # Configure file paths
    input_file = 'traffic_accidents_rev2'
    output_file = input_file + '_translated_pt.csv'
    
    # Ensure input exists
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file not found at {input_file}")
    else:
        translate_csv(input_file, output_file)


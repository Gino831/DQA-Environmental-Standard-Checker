import re
import csv
import json

def parse_data_js(file_path):
    standards = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find the JSON array within window.initialStandards = [...]
        # Remove the first line (console.log) and extract the array
        match = re.search(r'window\.initialStandards\s*=\s*(\[[\s\S]*\])\s*;?', content)
        if match:
            json_str = match.group(1)
            # Parse as JSON
            standards = json.loads(json_str)
        else:
            print("Could not find initialStandards array in data.js")
            return []
                
        return standards
            
    except Exception as e:
        print(f"Error parsing data.js: {e}")
        return []

def main():
    standards = parse_data_js('data.js')
    
    if not standards:
        print("No standards found.")
        return

    fieldnames = ['id', 'name', 'description', 'version', 'effectiveDate', 'expiryDate', 'cost', 'category', 'revisionSummary', 'sourceUrl', 'lastVerified', 'verifiedBy', 'stressType']
    
    with open('standards.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for std in standards:
            writer.writerow(std)
            
    print(f"Successfully exported {len(standards)} standards to standards.csv")

if __name__ == "__main__":
    main()

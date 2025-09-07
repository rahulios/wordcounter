import json
import csv
import pandas as pd
from datetime import datetime

def flatten_json_data(data):
    """
    Flattens nested JSON data into records suitable for CSV conversion
    """
    flattened_data = []
    
    # Iterate through each timestamp entry
    for entry in data:
        timestamp = entry['timestamp']
        
        # Process each asset in the entry
        for asset in entry['assets']:
            record = {
                'timestamp': timestamp,
                'asset': asset['symbol'],
                'price_usd': asset['priceUsd'],
                'apy': asset['apy'],
                'tvl_total': asset['tvlUsd']['total']
            }
            
            # Add individual chain TVLs if they exist
            chains = ['ethereum', 'solana', 'mantle', 'aptos', 'noble', 'arbitrum', 'sui']
            for chain in chains:
                record[f'tvl_{chain}'] = asset['tvlUsd'].get(chain, 0)
            
            flattened_data.append(record)
    
    return flattened_data

def json_to_csv(input_file, output_file):
    """
    Converts a JSON file to CSV format
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output CSV file
    """
    try:
        # Read JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Flatten the data
        flattened_data = flatten_json_data(data)
        
        # Get all unique keys to use as CSV headers
        headers = set()
        for record in flattened_data:
            headers.update(record.keys())
        headers = sorted(list(headers))
        
        # Write to CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(flattened_data)
        
        print(f"Successfully converted {input_file} to {output_file}")
        
    except Exception as e:
        print(f"Error converting file: {str(e)}")

# Alternative method using pandas
def json_to_csv_pandas(input_file, output_file):
    """
    Converts a JSON file to CSV format using pandas
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output CSV file
    """
    try:
        # Read JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Flatten the data
        flattened_data = flatten_json_data(data)
        
        # Convert to pandas DataFrame and save to CSV
        df = pd.DataFrame(flattened_data)
        df.to_csv(output_file, index=False)
        
        print(f"Successfully converted {input_file} to {output_file}")
        
    except Exception as e:
        print(f"Error converting file: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Using the basic CSV writer method
    json_to_csv('history.json', 'output.csv')
    
    # Or using the pandas method
    # json_to_csv_pandas('history.json', 'output_pandas.csv')
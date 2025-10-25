from pathlib import Path
import pandas as pd

def load_data(file_path):
    """Load data from a CSV file into a pandas DataFrame."""
    try:
        data = pd.read_csv(file_path)
        return data
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except pd.errors.EmptyDataError:
        print("Error: The file is empty.")
        return None
    except pd.errors.ParserError:
        print("Error: There was a parsing error while reading the file.")
        return None
    
def main():
    file_path = Path('../data/CIK.csv').resolve()
    data = load_data(file_path)
    
    if data is not None:
        print("Data loaded successfully:")
        print(data.head())
    else:
        print("Failed to load data.")
        
        
if __name__ == "__main__":
    main()
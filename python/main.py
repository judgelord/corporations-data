from pathlib import Path
import pandas as pd

def load_data(file_path):
    """Load data from CSV files into a pandas DataFrame."""
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
    file_names = ['CIK.csv', 'compustat_clean.csv', 'FDIC_clean.csv', 'SEC_Institutions.csv', 'CompustatNames.csv']  # Add other file names as needed
    for file_name in file_names:
        current_dir = Path(__file__).parent
        file_path = current_dir / '..' / 'data' / file_name
        file_path = file_path.resolve()
        data = load_data(file_path)

        if data is not None:
            print(f"{file_name} data loaded successfully:")
            print(data.head(20))  # Print first 20 rows
        else:
            print(f"Failed to load data from {file_name}.")

if __name__ == "__main__":
    main() 
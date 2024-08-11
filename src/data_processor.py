"""
Data Processor Module

This module handles data processing functionality using Pandas.
"""

# Implement data processing functions here
"""
Data Processing Module

This module handles data processing functionality using Pandas.
"""

import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessingError(Exception):
    """Custom exception class for data processing errors"""
    pass

def read_csv(file_path):
    """
    Read the CSV file and convert it to a Pandas DataFrame.

    Args:
        file_path (str): Path to the CSV file

    Returns:
        pd.DataFrame: DataFrame containing the CSV data

    Raises:
        DataProcessingError: If there's an error reading the CSV file
    """
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Successfully read CSV file: {file_path}")
        return df
    except Exception as e:
        logging.error(f"Error reading CSV file: {str(e)}")
        raise DataProcessingError(f"Failed to read CSV file: {str(e)}")

def clean_data(df):
    """
    Clean the data by handling inconsistencies and missing values.

    Args:
        df (pd.DataFrame): Input DataFrame

    Returns:
        pd.DataFrame: Cleaned DataFrame

    Raises:
        DataProcessingError: If there's an error during data cleaning
    """
    try:
        # Remove any leading/trailing whitespace from string columns
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        # Handle missing values (you may want to customize this based on your specific needs)
        df = df.fillna('N/A')

        # Ensure numeric columns are of the correct type
        numeric_columns = ['etr_rank', 'etr_pos_rank', 'adp', 'adp_pos_rank', 'adp_diff']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        logging.info("Data cleaning completed successfully")
        return df
    except Exception as e:
        logging.error(f"Error during data cleaning: {str(e)}")
        raise DataProcessingError(f"Failed to clean data: {str(e)}")

def transform_data(df):
    """
    Transform the data to match DraftKings format.

    Args:
        df (pd.DataFrame): Input DataFrame

    Returns:
        pd.DataFrame: Transformed DataFrame

    Raises:
        DataProcessingError: If there's an error during data transformation
    """
    try:
        # Load DraftKings pre-draft rankings
        dk_rankings = pd.read_csv('csv-templates/DkPreDraftRankings.csv')

        # Function to find the closest matching player ID
        def find_player_id(name, position):
            matches = dk_rankings[(dk_rankings['Name'].str.contains(name, case=False, na=False)) & 
                                  (dk_rankings['Position'] == position)]
            if not matches.empty:
                return matches.iloc[0]['ID']
            return None

        # Rename columns to match DraftKings format
        df = df.rename(columns={
            'name': 'Name',
            'team': 'Team',
            'position': 'Position',
            'etr_rank': 'ETR Rank',
            'etr_pos_rank': 'ETR Pos Rank',
            'adp': 'ADP',
            'adp_pos_rank': 'ADP Pos Rank',
            'adp_diff': 'ADP Diff'
        })

        # Add ID column by matching player names and positions
        df['ID'] = df.apply(lambda row: find_player_id(row['Name'], row['Position']), axis=1)

        # Reorder columns to match DraftKings format
        df = df[['ID', 'Name', 'Position', 'ADP', 'Team', 'ETR Rank', 'ETR Pos Rank', 'ADP Pos Rank', 'ADP Diff']]

        # Fill any missing values with empty strings
        df = df.fillna('')

        logging.info("Data transformation completed successfully")
        return df
    except Exception as e:
        logging.error(f"Error during data transformation: {str(e)}")
        raise DataProcessingError(f"Failed to transform data: {str(e)}")

def process_data(data):
    """
    Main function to process the data: read CSV or use provided data, clean, and transform.

    Args:
        data (str or list): Path to the CSV file or list of dictionaries containing player data

    Returns:
        pd.DataFrame: Processed DataFrame

    Raises:
        DataProcessingError: If there's an error during any step of data processing
    """
    try:
        if isinstance(data, str):
            df = read_csv(data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            raise DataProcessingError(f"Invalid data type: {type(data)}. Expected str or list.")
        
        df = clean_data(df)
        df = transform_data(df)
        logging.info("Data processing completed successfully")
        return df
    except DataProcessingError as e:
        logging.error(f"Data processing failed: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during data processing: {str(e)}")
        return None

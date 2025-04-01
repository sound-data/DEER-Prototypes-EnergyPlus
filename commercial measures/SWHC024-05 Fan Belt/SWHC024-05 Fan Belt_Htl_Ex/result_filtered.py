# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 08:27:33 2024

@author: afaramarzi
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 07:56:49 2024

@author: afaramarzi
"""

import pandas as pd

class CoilListProcessor:
    def __init__(self, normunit, excel_file_path, sizing_detail_csv):
        self.normunit = normunit
        self.excel_file_path = excel_file_path
        self.sizing_detail_csv = sizing_detail_csv
    
    def read_data(self):
        # Read coil list Excel file and sizing detail CSV file
        self.coil_list_df = pd.read_excel(self.excel_file_path)
        self.sim_sizing_data = pd.read_csv(self.sizing_detail_csv)
    
    def process_data(self):
        # Extract building prototype from file name
        self.sim_sizing_data['building type'] = self.sim_sizing_data['File Name'].str.extract(r'/([A-Za-z0-9]+)&')
        
        # Merge the sizing detail data with the coil list data based on row name and building type
        self.df_filtered = pd.merge(self.sim_sizing_data,
                                    self.coil_list_df,
                                    left_on=['RowName', self.sim_sizing_data['building type'].str.lower()],
                                    right_on=['cooling coil name', self.coil_list_df['building type'].str.lower()])
        
        # Aggregate the filtered dataframe by adding up desired normunits based on file names
        self.sizing_agg_filtered = self.df_filtered.groupby(['File Name'])['Value'].sum()
        self.sizing_agg_filtered.name = self.normunit
        
    def save_processed_data(self, output_csv):
        # Save the aggregated data to a CSV file
        self.sizing_agg_filtered.to_csv(output_csv, index=True)


def process_coil_list(normunit, excel_file_path, sizing_detail_csv, output_csv):
    # Initialize and process data using CoilListProcessor class
    processor = CoilListProcessor(normunit, excel_file_path, sizing_detail_csv)
    processor.read_data()
    processor.process_data()
    processor.save_processed_data(output_csv)
    print(f"script ran successfully")

# Example usage:
if __name__ == "__main__":
    normunit = "Cooling Capacity (W)"
    excel_file_path = 'coil_list.xlsx'
    sizing_detail_csv = 'results-sizing-detail.csv'
    output_csv = 'sizing_agg_filtered.csv'

    process_coil_list(normunit, excel_file_path, sizing_detail_csv, output_csv)

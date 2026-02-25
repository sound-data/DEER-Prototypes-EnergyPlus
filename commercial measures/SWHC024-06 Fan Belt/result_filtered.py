# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 08:27:33 2024

@author: afshin faramarzi
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 07:56:49 2024

@author: afshin faramarzi
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
        # Convert 'Value' column to numeric, forcing errors to NaNs
        self.sim_sizing_data['Value'] = pd.to_numeric(self.sim_sizing_data['Value'], errors='coerce')
        
        # Drop rows with NaN 'Value'
        self.sim_sizing_data.dropna(subset=['Value'], inplace=True)

        # Extract building prototype from file name
        self.sim_sizing_data['building type'] = self.sim_sizing_data['File Name'].str.extract(r'/([A-Za-z0-9]+)&')
        
        # Merge the sizing detail data with the coil list data based on row name and building type
        self.df_filtered = pd.merge(self.sim_sizing_data,
                                    self.coil_list_df,
                                    left_on=['RowName', self.sim_sizing_data['building type'].str.lower()],
                                    right_on=['object name', self.coil_list_df['building type'].str.lower()])
        
        # Aggregate the filtered dataframe by adding up desired normunits based on file names
        # Outputs a pandas.Series indexed by filename
        series_agg_values = self.df_filtered.groupby(['File Name'])['Value'].sum()
        series_agg_values.name = self.normunit
        # Drop the index to a regular column named 'File Name'
        # Outputs a pandas.DataFrame
        df1 = series_agg_values.reset_index()

        # Get additional metadata from filename based on DEER prototypes conventions
        # Outputs a pandas.DataFrame
        pattern = r'(?P<BldgLoc>CZ\d\d)/(?P<BldgType>\w+)&(?P<Story>\w+)&(?P<BldgHVAC>\w+)&(?P<BldgVint>\w+)&(?P<TechGroup>\w+)__(?P<TechType>\w+)/(?P<TechID>[^/]+)/instance.*'
        #pattern = r'(?P<BldgLoc>CZ\d\d)/(?P<Cohort>[^/]+)/(?P<Case>[^/]+)/instance.*'
        df2 = df1['File Name'].str.extract(pattern)
        df2.set_index(df1.index)
        self.sizing_agg_filtered = pd.concat([df1, df2],axis=1)
        
    def save_processed_data(self, output_csv):
        # Save the aggregated data to a CSV file
        self.sizing_agg_filtered.to_csv(output_csv, index=False)


def process_coil_list(normunit, excel_file_path, sizing_detail_csv, output_csv):
    # Initialize and process data using CoilListProcessor class
    processor = CoilListProcessor(normunit, excel_file_path, sizing_detail_csv)
    print(f"Reading from '{excel_file_path}' and '{sizing_detail_csv}' ...")
    processor.read_data()
    print(f"Filtering objects and calculating aggregated sum ...")
    processor.process_data()
    print(f"Writing '{output_csv}' ...")
    processor.save_processed_data(output_csv)
    print("Done.")

# Example usage:
if __name__ == "__main__":
    normunit = "Cooling Capacity (W)"
    excel_file_path = 'coil_list.xlsx'


    sizing_detail_csv = 'SWHC024-06 Fan Belt_Ex/results-sizing-detail.csv'
    output_csv = 'SWHC024-06 Fan Belt_Ex/sizing_agg_filtered.csv'
    process_coil_list(normunit, excel_file_path, sizing_detail_csv, output_csv)

    sizing_detail_csv = 'SWHC024-06 Fan Belt_Htl_Ex/results-sizing-detail.csv'
    output_csv = 'SWHC024-06 Fan Belt_Htl_Ex/sizing_agg_filtered.csv'
    process_coil_list(normunit, excel_file_path, sizing_detail_csv, output_csv)

    sizing_detail_csv = 'SWHC024-06 Fan Belt_Htl_New/results-sizing-detail.csv'
    output_csv = 'SWHC024-06 Fan Belt_Htl_New/sizing_agg_filtered.csv'
    process_coil_list(normunit, excel_file_path, sizing_detail_csv, output_csv)

    sizing_detail_csv = 'SWHC024-06 Fan Belt_New/results-sizing-detail.csv'
    output_csv = 'SWHC024-06 Fan Belt_New/sizing_agg_filtered.csv'
    process_coil_list(normunit, excel_file_path, sizing_detail_csv, output_csv)

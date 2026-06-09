# %%
import pandas as pd
import os
import re

weights_df = pd.read_csv('weights_by_vintage.csv')
weights = dict(zip(weights_df['BldgVint'], weights_df['Weight']))

climate_weights_df = pd.read_csv('weights_by_vintage_climate.csv')
climate_weights = dict(zip(zip(climate_weights_df['BldgVint'], climate_weights_df['BldgLoc']), climate_weights_df['Weight']))

def parse_csv(file_path):
    year = int(re.search(r'_(\d{4})\.csv', file_path).group(1))
    with open(file_path, 'r') as file:
        lines = file.readlines()

    tables = []
    table = []
    for line in lines:
        if re.match(r'^[^a-zA-Z0-9]', line):
            continue
        if 'table:' in line:
            if table:  
                tables.append(table)
                table = []
        table.append(line.strip())  
    if table: 
        tables.append(table)

    # Convert each table into a dataframe in a structure
    structures ={
            'table': [],
            'dataframe': [],
            'vintage':[]
        }
    count = 0
    for table in tables:
        table_name = table[0]
        df = pd.DataFrame([x.split(',') for x in table[2:]], columns=table[1].split(','))
        df = df.loc[:, df.columns != '']    # Remove unlabaled columns
        structures['table'].append(table_name)
        structures['dataframe'].append(df)
        if count == 0:
            structures['vintage'].append(year)
        count += 1
    return structures
#%%
# Get a list of all csv files in the 'codes' folder starting with 'T24' and ending with '.csv'
csv_files = [os.path.join('codes/others', f) for f in os.listdir('codes/others') if f.startswith('T24') and f.endswith('.csv')]

all_structures = []
for csv_file in csv_files:#[csv_files[0],csv_files[6]]:
    # weight = weights[year]  # Get the weight for the year
    structures = parse_csv(csv_file)  # Parse the csv file
    all_structures.append(structures)
# %%
df_dataset = pd.DataFrame(columns=['Vintage_year', 'Table_name', 'Row_name', 'Column', 'Value','Weight'])

for structures_vin in all_structures:
    for index, tbl in enumerate(structures_vin['table']):
        vin = structures_vin['vintage'][0]
        tbl_name = tbl
        dataframe = structures_vin['dataframe'][index]
        for col in dataframe.columns[1:]:
            for index, row in dataframe.iterrows():
                row_name = row[dataframe.columns[0]]
                col_name = col
                param_value = row[col]
                climate_zone = re.search(r'Climate Zone (\d+),', tbl)
                if climate_zone:
                    weight = climate_weights[(vin, int(climate_zone.group(1)))]
                    cz = int(climate_zone.group(1))
                else:
                    if dataframe.columns[0] == 'Climate Zone':
                        weight = climate_weights[(vin, int(row_name))]
                        cz = int(row_name)
                    else:
                        weight = weights[vin]
                        cz = None
                new_row = {'Vintage_year': vin, 'Table_name': tbl_name, 'Row_name': row_name,'Column': col_name, 'Value': param_value, 'Weight': weight, 'CZ': cz}
                df_dataset = pd.concat([df_dataset, pd.DataFrame(new_row, index=[0])], ignore_index=True)
# %%
        
with open('combined_vintages_others.csv', 'w') as f:
    for tbl in df_dataset['Table_name'].unique():
        f.write(tbl + '\n')
        column_names = df_dataset.loc[df_dataset['Table_name'] == tbl, 'Column'].unique()
        f.write(',' + ','.join(column_names)+'\n')

        row_names = df_dataset.loc[df_dataset['Table_name'] == tbl, 'Row_name'].unique()
        for row in row_names:
            weighted_average_list = []
            for col in column_names:
                filtered_df = df_dataset[(df_dataset['Row_name'] == row) & (df_dataset['Column'] == col) & (df_dataset['Table_name'] == tbl)]
                # Filter rows with NaN or string values in the 'Value' column
                filtered_df['Value'] = pd.to_numeric(filtered_df['Value'], errors='ignore')

                filtered_rows_index = filtered_df['Value'].apply(lambda x: isinstance(x, str))

                # Set weights to 0 for the filtered rows
                filtered_df.loc[filtered_rows_index, ['Weight','Value']] = 0
                if filtered_df['Weight'].sum() == 0:
                    weighted_average = ''
                else:
                    weighted_average = (filtered_df['Value'] * filtered_df['Weight']).sum() / filtered_df['Weight'].sum()
                weighted_average_list.append(str(weighted_average))
            f.write(row + ',' + ','.join(weighted_average_list)+'\n')
        f.write('\n')

# %%

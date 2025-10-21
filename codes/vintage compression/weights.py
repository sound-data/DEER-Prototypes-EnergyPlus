
# %%
import pandas as pd

df = pd.read_excel("original_weights_Others.xlsx")

# Calculate the sums of weights for each vintage (BldgVint)
weights_by_vintage = df.groupby('BldgVint')['weight'].sum()

# Create a new DataFrame for weights by vintage
weights_by_vintage_df = pd.DataFrame({
    'BldgVint': weights_by_vintage.index,
    'Weight': weights_by_vintage
})

# Calculate the sums of weights for each vintage and CZ (BldgLoc)
weights_by_vintage_climate = df.groupby(['BldgVint', 'BldgLoc'])['weight'].sum()

# Create a new DataFrame for weights by vintage and CZ
weights_by_vintage_climate_df = pd.DataFrame({
    'BldgVint': weights_by_vintage_climate.index.get_level_values('BldgVint'),
    'BldgLoc': weights_by_vintage_climate.index.get_level_values('BldgLoc'),
    'Weight': weights_by_vintage_climate
})

weights_by_vintage_df.to_csv('weights_by_vintage.csv', index=False)
weights_by_vintage_climate_df.to_csv('weights_by_vintage_climate.csv', index=False)

# %%

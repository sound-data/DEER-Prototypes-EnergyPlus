#%%
import pandas as pd
import numpy as np
import plotly.graph_objects as go
# %%
#Function to create interactive Plotly figure of hourly loadshapes for a given building type, 
#with one line per unique Descriptor (combination of BldgType, BldgVint, BldgHVAC, BldgLoc, TechID)
def plot_hourly_loadshapes(df, bldgtype, y_title="Hourly Energy Consumption, kWh", output_html: str | None = None):     
    # -----------------------------
    # 1) Build figure (one trace per Descriptor)
    # -----------------------------
    fig = go.Figure()

    for desc, g in df.groupby("Descriptor", sort=False):
        g = g.sort_values("timestamp")
        fig.add_trace(go.Scatter(
            x=g["timestamp"],
            y=g["hourly_consumption"],
            mode="lines",
            name=str(desc),
            line=dict(width=1), 
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Time: %{x|%Y-%m-%d %H:%M}<br>"
                "Hrly Consumption: %{y:.8f}<br>"
                "<extra></extra>"
            ),
            customdata=[desc] * len(g) #hover label setting

        ))

    # -----------------------------
    # 2) Layout: range selector, rangeslider, legend on the right
    # -----------------------------
    fig.update_layout(
        title=f"{bldgtype} Hourly Whole-building Load Shapes",
        template="simple_white",

        xaxis=dict(
            title="Date-Time",
            type="date",
            rangeselector=dict(
                x=1.0,            # right edge
                y=1.0,            # top edge
                xanchor="right",
                yanchor="top",

                buttons=[
                    dict(count=1, step="day",   stepmode="backward", label="1d"),
                    dict(count=7, step="day",   stepmode="backward", label="1w"),
                    dict(count=1, step="month", stepmode="backward", label="1m"),
                    dict(step="all", label="All"),
                ]
            ),
            rangeslider=dict(visible=True)
        ),
        yaxis=dict(title=y_title),

        # Legend on the right (vertical list)
        legend=dict(
            orientation="v",
            x=1.02,      # push legend to the right side
            xanchor="left",
            y=1.0,
            yanchor="top",
            bgcolor="rgba(255,255,255,0.6)"  # subtle background for readability
        ),

        # Leave decent right margin so the legend doesn't overlap the plot
        #margin=dict(l=60, r=220, t=60, b=60),
    )

    # Compact legend outside on the right, maximize canvas
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top", y=0.78,
            xanchor="left", x=1.02,          # outside on the right
            font=dict(size=9),               # compact font
            itemsizing="constant",           # consistent row height
            bgcolor="rgba(255,255,255,0.8)", # readable over any background
            bordercolor="#ccc",
            borderwidth=1,
            itemwidth=80,                    # (optional) constrain label width for tighter wrapping
        ),
    )

    
    fig.update_layout(
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(255,255,255,0.9)", 
                font_size=11
            )
        ) #show all hover labels
    
    
    instructions = (
        "<b>Tips</b><br>"
        "1. Click inside the legend to select/unselect load shapes.<br>"
        "2. Double-click a legend item to isolate one load shape.<br>"
        "3. To zoom in/out quickly, use gray buttons to the immediate<br> left or select range with mouse (left-click + drag horizontally).<br>"
        "4. To adjust the range of the zoomed-in data shown,<br> use the lower Date-Time chart."
    )

    right_gutter = 380
    fig.update_layout(margin=dict(l=10, r=right_gutter, t=60, b=40))

    fig.add_annotation(
        x=1.02, y=1.0,                  # position near upper-right (paper coords)
        xref="paper", yref="paper",
        xanchor="left", yanchor="top",
        align="left",
        text=instructions,
        showarrow=False,
        font=dict(size=10, color="#111"),
        bgcolor="rgba(255,255,255,0.90)",
        bordercolor="#ccc",
        borderwidth=1,
        borderpad=8
    )

    if output_html:
            fig.write_html(output_html, include_plotlyjs="cdn")


    return fig


#Function to prep data for plotting:

#create hourly consumption table
def calc_hourly_consumption(annual_csv, unitized_csv):
    #read data
    df_annual = pd.read_csv(annual_csv)
    df_unitized = pd.read_csv(unitized_csv)

    #create lookup dict key for annual values
    id_cols = ['BldgType', 'BldgVint', 'BldgHVAC', 'BldgLoc', 'TechID']
    annual_lookup = df_annual.set_index(id_cols)['annual_sum'].to_dict()
    
    #map annual data into loadshape table
    keys = list(map(tuple, df_unitized[id_cols].to_numpy()))
    df_unitized['annual_sum'] = pd.Series(keys).map(annual_lookup).to_numpy()

    #apply annual sum
    #making sure total sum back to annual sum by adjusting with actual sum of UECproportion
    group_sum = df_unitized.groupby(id_cols)['UECproportion'].transform('sum')
    scale = df_unitized['annual_sum'] / group_sum.replace(0, np.nan)
    df_unitized['hourly_consumption'] = (df_unitized['UECproportion'] * scale).astype('float32')

    return df_unitized


#Creates a timestamp column from Source Year and Hour of Year, and a Descriptor column for grouping
def cedars_data_loader_pre_plot(input_df):
    df = input_df
    df['Descriptor'] = df['BldgType'] + '|' + df['BldgVint'] + '|' + df['BldgHVAC'] + '|' + df['BldgLoc'] + '|' + df['TechID']
    
    # Ensure numeric
    df["Source Year"] = pd.to_numeric(df["Source Year"], errors="coerce")
    df["Hour of Year"] = pd.to_numeric(df["Hour of Year"], errors="coerce")

    # Use the row's own Source Year if it varies; otherwise this still works.
    # Timestamp = Jan 1 of that year + (hour-1) hours
    base = pd.to_datetime(df["Source Year"].astype("Int64").astype(str) + "-01-01", errors="coerce")
    df["timestamp"] = base + pd.to_timedelta(df["Hour of Year"] - 1, unit="h")

    # --- sort by time just to be safe ---
    df = df.sort_values(['BldgType', 'BldgVint', 'BldgHVAC', 'BldgLoc','TechID', 'timestamp'])
    
    return df

#%%
#indicate input CSV file names (CEDARS processed format)
unitized_dmo = 'CEDARS_long_ls_DMo.csv'
unitized_mfm = 'CEDARS_long_ls_MFm.csv'
unitized_sfm = 'CEDARS_long_ls_SFm.csv'
unitized_com = 'CEDARS_long_ls_Com.csv'

annual_dmo = 'CEDARS_ls_annual_loads_DMo.csv'
annual_mfm = 'CEDARS_ls_annual_loads_MFm.csv'
annual_sfm = 'CEDARS_ls_annual_loads_SFm.csv'
annual_com = 'CEDARS_ls_annual_loads_Com.csv'


#%%
#produce hourly consumption col

input_dmo = None
input_mfm = None
input_sfm = None
input_com = None

try:
    input_dmo = calc_hourly_consumption(annual_dmo, unitized_dmo)
    print("DMo data loaded.")
except FileNotFoundError:
    print("DMo files not found, skipping DMo.")

try:
    input_mfm = calc_hourly_consumption(annual_mfm, unitized_mfm)
    print("MFm data loaded.")
except FileNotFoundError:
    print("MFm files not found, skipping MFm.")

try:
    input_sfm = calc_hourly_consumption(annual_sfm, unitized_sfm)
    print("SFm data loaded.")
except FileNotFoundError:
    print("SFm files not found, skipping SFm.")

try:
    input_com = calc_hourly_consumption(annual_com, unitized_com)
    print("Com data loaded.")
except FileNotFoundError:
    print("Com files not found, skipping Com.")

#%%
#Residential plots
#stacking 3 dfs on top of each other, if they exists
res_parts = [x for x in [input_dmo, input_mfm, input_sfm] if x is not None]
if len(res_parts) == 0:
    print("No Res data, please provide both 'CEDARS_long_ls_*.csv' and 'CEDARS_ls_annual_loads_*.csv' in the same folder.")
else:
    input_res = pd.concat(res_parts, ignore_index=True)
    df_res = cedars_data_loader_pre_plot(input_res)
    #loop thru residential building types and export separate html for each
    for bldgtype in df_res['BldgType'].unique():
        print(f"Creating Plotly html for {bldgtype}...")
        df_bldg = df_res[df_res['BldgType'] == bldgtype]
        techgroup = df_bldg['TechGroup'].unique()[0]
        techtype = df_bldg['TechType'].unique()[0]
        output_html = f"{bldgtype}_WB_{techgroup}_{techtype}_Load_Shapes.html"
        plot_hourly_loadshapes(df_bldg, bldgtype=bldgtype, y_title="Hourly Energy Consumption, kWh", output_html=output_html)
        print("plot created.")


# %%
#Commercial plots

if input_com is None:
    print("No Com data, please provide both 'CEDARS_long_ls_Com.csv' and 'CEDARS_ls_annual_loads_Com.csv' in the same folder. Com skipped.")
else:
    df_com = cedars_data_loader_pre_plot(input_com)
    #loop thru commercial building types and export separate html for each
    for bldgtype in df_com['BldgType'].unique():
        print(f"Creating Plotly html for {bldgtype}...")
        df_bldg = df_com[df_com['BldgType'] == bldgtype]
        techgroup = df_bldg['TechGroup'].unique()[0]
        techtype = df_bldg['TechType'].unique()[0]
        output_html = f"{bldgtype}_WB_{techgroup}_{techtype}_Load_Shapes.html"
        plot_hourly_loadshapes(df_bldg, bldgtype=bldgtype, y_title="Hourly Energy Consumption, kWh", output_html=output_html)
        print("plot created.")

#%%
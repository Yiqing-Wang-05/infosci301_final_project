from dash import Dash, dcc, html
import plotly.express as px
import pandas as pd
from pathlib import Path

app = Dash(__name__)
DATA_DIR = Path("https://github.com/Yiqing-Wang-05/infosci301_final_project/")

# --- World Bank Data Loader ---
def read_wb(path: Path, var_name: str) -> pd.DataFrame:
    xls = pd.ExcelFile(path)
    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0], header=None)
    df.columns = df.iloc[4]
    df = df.iloc[5:].rename(columns={
        df.columns[0]: "Country",
        df.columns[1]: "Country Code"
    })
    df = df.melt(id_vars=["Country","Country Code"], var_name="Year", value_name=var_name)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df[var_name] = pd.to_numeric(df[var_name], errors="coerce")
    return df.dropna(subset=["Year"])

# Load data
gdp   = read_wb(DATA_DIR/"GDP.xlsx",       "GDP_USD")
edu   = read_wb(DATA_DIR/"Government expenditure on education as % of GDP (%).xlsx", "Edu_pct_GDP")
urban = read_wb(DATA_DIR/"Urban population (% of total population).xlsx", "Urban_pct")

country_map = pd.read_excel(DATA_DIR/"OPRI_COUNTRY.xlsx").rename(columns={
    "COUNTRY_ID": "Country Code", "COUNTRY_NAME_EN": "Country"
})

raw = pd.read_excel(DATA_DIR/"inbound and outbound of international students.xlsx", sheet_name="data")
flows = {26637: "Inbound", 26519: "Outbound"}

mig = (
    raw[raw["indicatorId"].isin(flows)]
       .rename(columns={"geoUnit": "Country Code", "year": "Year", "value": "Students"})
       .assign(Type=lambda df: df["indicatorId"].map(flows))
       .dropna(subset=["Year","Students"])
       .merge(country_map, on="Country Code", how="left")
       .dropna(subset=["Country"])
)

mig_wide = mig.pivot_table(index=["Country","Year"], columns="Type", values="Students", aggfunc="first").reset_index()

# Merge everything
df = (mig_wide
    .merge(gdp, on=["Country", "Year"], how="left")
    .merge(edu, on=["Country", "Year"], how="left")
    .merge(urban, on=["Country", "Year"], how="left")
)

df = df[df["Year"].between(2000, 2022)]
long = df.melt(
    id_vars=["Country", "Year", "GDP_USD", "Edu_pct_GDP", "Urban_pct"],
    value_vars=["Inbound", "Outbound"],
    var_name="Type", value_name="Students"
).dropna(subset=["Students"])

long["Year"] = long["Year"].astype(str)
color_map = {"Inbound": "blue", "Outbound": "red"}
years = sorted(long["Year"].unique())

fig = px.scatter_geo(
    long,
    locations="Country", locationmode="country names",
    size="Students", color="Type", color_discrete_map=color_map,
    hover_name="Country",
    hover_data={"Students":":,", "GDP_USD":":,.0f", "Edu_pct_GDP":":.1f", "Urban_pct":":.1f", "Type":False, "Year":False},
    animation_frame="Year", projection="natural earth", size_max=40,
    template="plotly_white", category_orders={"Year": years},
    title="\U0001F310 International Student Migration (2000–2022)<br><sub>Blue = Inbound | Red = Outbound</sub>"
)

fig.update_traces(marker=dict(opacity=0.6, line_width=0.5, line_color="darkgrey"))
fig.update_geos(showcountries=True, countrycolor="lightgray", showland=True, landcolor="whitesmoke", showocean=True, oceancolor="lightblue")
fig.update_layout(margin=dict(l=0, r=0, t=70, b=0), legend_title_text="Flow Type")

app.layout = html.Div([
    html.H1("International Student Migration Dashboard"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run(debug=True)

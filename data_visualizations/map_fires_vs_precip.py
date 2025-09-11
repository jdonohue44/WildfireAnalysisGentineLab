# Creating animated US choropleth with wildfire and precipitation dots (mock data)
# The figure will animate year-by-year from 2000 to 2025.
# Uses Plotly to create a choropleth of precipitation (per-state) and two scattergeo layers:
#  - wildfire events (colorscale = 'YlOrRd', intensity encoded)
#  - precipitation event dots (colorscale = 'Blues', intensity encoded)
# Data is mock but structured plausibly. Reproducible via random seed.

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

np.random.seed(42)

# 50 US states + DC abbreviations
states = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS",
          "KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM",
          "NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA",
          "WA","WV","WI","WY","DC"]

years = list(range(2000, 2026))  # 2000-2025 inclusive

# Assign simple region categories to bias precipitation / wildfire baselines
west = {"CA","OR","WA","NV","AZ","NM","CO","UT","ID","MT","WY"}
southeast = {"FL","GA","AL","MS","LA","SC","NC","TN","KY"}
northeast = {"ME","NH","VT","MA","RI","CT","NY","NJ","PA","MD","DE"}
midwest = {"OH","MI","IN","IL","WI","MN","IA","MO","ND","SD","NE","KS"}
islands = {"HI","AK"}

# base precipitation (mm) and wildfire count baselines
base_precip = {}
base_wild = {}
for st in states:
    if st in west:
        base_precip[st] = np.random.normal(600, 120)   # moderate
        base_wild[st] = np.random.uniform(30, 80)      # higher wildfire baseline
    elif st in southeast:
        base_precip[st] = np.random.normal(1300, 200)  # high precip
        base_wild[st] = np.random.uniform(5, 25)
    elif st in northeast:
        base_precip[st] = np.random.normal(1100, 200)
        base_wild[st] = np.random.uniform(2, 15)
    elif st in midwest:
        base_precip[st] = np.random.normal(900, 180)
        base_wild[st] = np.random.uniform(3, 20)
    elif st in islands:
        base_precip[st] = np.random.normal(1500, 300)
        base_wild[st] = np.random.uniform(1, 10)
    else:
        base_precip[st] = np.random.normal(800, 200)
        base_wild[st] = np.random.uniform(2, 30)

# Build DataFrame of per-state, per-year summary metrics
rows = []
for year in years:
    # add a mild trend: precip slightly variable; wildfire increasing slightly over years
    year_frac = (year - 2000)/25.0  # 0->1 across 2000-2025
    for st in states:
        # precipitation amount (mm) with random noise and year-to-year variability
        precip = base_precip[st] * (1 + np.random.normal(0, 0.08)) * (1 + (np.random.normal(0, 0.03) * year_frac))
        # wildfire count/area index with upward trend for recent years (climate-driven)
        wild = base_wild[st] * (1 + 0.9*year_frac) * (1 + np.random.normal(0, 0.25))
        # Add occasional big wildfire spikes in western states in later years
        if (st in west) and (np.random.rand() < 0.08 + 0.12*year_frac):
            wild *= np.random.uniform(1.5, 4.0)
        rows.append({
            "state": st,
            "year": year,
            "precip_mm": max(0, precip),
            "wildfire_index": max(0, wild)
        })

df = pd.DataFrame(rows)

# Normalize intensities to 0-1 per metric for color mapping across all years
df["precip_intensity"] = (df["precip_mm"] - df["precip_mm"].min()) / (df["precip_mm"].max() - df["precip_mm"].min())
df["wildfire_intensity"] = (df["wildfire_index"] - df["wildfire_index"].min()) / (df["wildfire_index"].max() - df["wildfire_index"].min())

# Create frames for animation: one frame per year
frames = []
zmin_precip = df["precip_intensity"].min()
zmax_precip = df["precip_intensity"].max()
cmin_wild = df["wildfire_intensity"].min()
cmax_wild = df["wildfire_intensity"].max()

for year in years:
    dyear = df[df["year"] == year].set_index("state").reindex(states).reset_index()
    # choropleth for precipitation (per-state), using intensity
    chor = go.Choropleth(
        locations=dyear["state"],
        z=dyear["precip_intensity"],
        locationmode="USA-states",
        zmin=zmin_precip,
        zmax=zmax_precip,
        colorscale="Blues",
        colorbar=dict(title="Precip intensity", len=0.4, y=0.9),
        marker_line_color='white',
        marker_line_width=0.5,
        showscale=False  # hide per-frame colorbar to avoid duplication in animation frames
    )
    # scattergeo for wildfire events
    scatter_wild = go.Scattergeo(
        locations=dyear["state"],
        locationmode="USA-states",
        text=[f"{s}: {w:.1f}" for s,w in zip(dyear["state"], dyear["wildfire_index"])],
        hoverinfo="text",
        marker=dict(
            size=4 + (dyear["wildfire_intensity"] * 20),  # scale marker size
            color=dyear["wildfire_intensity"],
            colorscale="YlOrRd",
            cmin=cmin_wild,
            cmax=cmax_wild,
            colorbar=dict(title="Wildfire intensity", len=0.4, y=0.45),
            line_width=0
        ),
        name="Wildfires"
    )
    # scattergeo for precipitation events (dots)
    scatter_precip = go.Scattergeo(
        locations=dyear["state"],
        locationmode="USA-states",
        text=[f"{s}: {p:.0f} mm" for s,p in zip(dyear["state"], dyear["precip_mm"])],
        hoverinfo="text",
        marker=dict(
            size=4 + (dyear["precip_intensity"] * 15),
            color=dyear["precip_intensity"],
            colorscale="Blues",
            cmin=zmin_precip,
            cmax=zmax_precip,
            colorbar=dict(title="Precip intensity (pts)", len=0.4, y=0.15),
            symbol="circle",
            line_width=0
        ),
        name="Precipitation events"
    )
    frames.append(go.Frame(data=[chor, scatter_wild, scatter_precip], name=str(year)))

# Create initial data for the first year
init = df[df["year"] == years[0]].set_index("state").reindex(states).reset_index()

fig = go.Figure(
    data=[
        go.Choropleth(
            locations=init["state"],
            z=init["precip_intensity"],
            locationmode="USA-states",
            zmin=zmin_precip,
            zmax=zmax_precip,
            colorscale="Blues",
            marker_line_color='white',
            marker_line_width=0.5,
            showscale=True,
            colorbar=dict(title="Precip intensity", len=0.5)
        ),
        go.Scattergeo(
            locations=init["state"],
            locationmode="USA-states",
            text=[f"{s}: {w:.1f}" for s,w in zip(init["state"], init["wildfire_index"])],
            hoverinfo="text",
            marker=dict(
                size=4 + (init["wildfire_intensity"] * 20),
                color=init["wildfire_intensity"],
                colorscale="YlOrRd",
                cmin=cmin_wild,
                cmax=cmax_wild,
                colorbar=dict(title="Wildfire intensity", len=0.4, y=0.5)
            ),
            name="Wildfires"
        ),
        go.Scattergeo(
            locations=init["state"],
            locationmode="USA-states",
            text=[f"{s}: {p:.0f} mm" for s,p in zip(init["state"], init["precip_mm"])],
            hoverinfo="text",
            marker=dict(
                size=4 + (init["precip_intensity"] * 15),
                color=init["precip_intensity"],
                colorscale="Blues",
                cmin=zmin_precip,
                cmax=zmax_precip,
                colorbar=dict(title="Precip intensity (pts)", len=0.4, y=0.2)
            ),
            name="Precipitation events"
        )
    ],
    layout=go.Layout(
        title_text="US precipitation (choropleth) with wildfire & precipitation dots — animated by year (2000–2025)",
        geo=dict(scope="usa", projection_type="albers usa"),
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=0,
            x=0.1,
            xanchor="right",
            yanchor="top",
            pad=dict(t=60, r=10),
            buttons=[dict(label="Play", method="animate", args=[None, {"frame": {"duration": 700, "redraw": True}, "fromcurrent": True, "transition": {"duration": 300}}])]
        )],
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01)
    ),
    frames=frames
)

# Add year slider
sliders = [{
    "active": 0,
    "pad": {"t": 50},
    "steps": [
        {"args": [[str(y)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
         "label": str(y),
         "method": "animate"} for y in years
    ]
}]
fig.update_layout(sliders=sliders)

# Show the figure
fig.show()

# Also provide a small preview table of the first few rows of the generated data
import caas_jupyter_tools as cjt
preview = df.sample(8, random_state=1).sort_values(["year","state"]).reset_index(drop=True)
cjt.display_dataframe_to_user("Sample of generated wildfire/precip data", preview)

# Evaluating Seasonal Precipitation on Wildfire Risk in the Western U.S.

This project investigates the relationship between seasonal precipitation patterns, cloud seeding interventions, and wildfire activity in the western United States. Using causal inference methods, we aim to understand how reduce wildfire risk can be better understood in fire-prone regions.

## Data Sources

1. US Cloud Seeding Activities (2000–2025) ([Zenodo](https://zenodo.org/records/16754931))
2. US Wildfires (1992-2015) ([Kaggle](https://www.kaggle.com/datasets/rtatman/188-million-us-wildfires/data))
3. US Precipitation (2000-2015) ([NOAA](https://www.ncei.noaa.gov/cdo-web/datasets))

## Research Questions

1. **Snowpack Effects**: Does increased snowpack reduce wildfires in subsequent fire seasons?
2. **Cloud Seeding Effects**: Do areas that are cloud-seeded experience fewer wildfires than those that are not?
3. **Optimal Deployment**:
   * When and where can cloud seeding be deployed to most effectively reduce wildfire risk?
   * Should seeding target warm-season or cold-season events, snowpack or rainfall?
   * What are the most optimal locations to cloud seed, given limited resources (e.g., areas near critical dryness thresholds)?

## Approach

We apply **causal inference methods** to evaluate how precipitation—natural and induced—affects wildfire outcomes across different regions and timeframes. The goal is to generate actionable insights for wildfire risk reduction and inform decisions about targeted precipitation enhancement strategies.

- Causal Discovery
- Difference in Differences
- Synthetic Control

## Project Structure

* **data_visualizations**: Contains python-based data visualizations (mostly chloropleth) to show wildfires vs precipitation
* **data**: Contains data sources


import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Handwashing dashboard',
    page_icon=':soap:',
)


@st.cache_data
def get_handwashing_data():
    """Load handwashing data from `data/handwashing.csv` and compute mortality rate.

    The expected CSV has columns: Year, Birth, Deaths, Clinic
    Returns a DataFrame with a computed `MortalityRate` percentage (Deaths / Birth * 100).
    """
    import os
    
    # Build path relative to this script's directory
    script_dir = Path(__file__).resolve().parent
    data_path = script_dir / 'data' / 'handwashing.csv'
    
    # If that doesn't exist, try relative to cwd (for Streamlit Cloud)
    if not data_path.exists():
        data_path = Path('data/handwashing.csv').resolve()
    
    if not data_path.exists():
        raise FileNotFoundError(
            f"handwashing.csv not found at {script_dir / 'data' / 'handwashing.csv'} or {Path('data/handwashing.csv').resolve()}"
        )
    
    df = pd.read_csv(str(data_path))

    # Ensure numeric types
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
    df['Birth'] = pd.to_numeric(df['Birth'], errors='coerce')
    df['Deaths'] = pd.to_numeric(df['Deaths'], errors='coerce')

    # Mortality rate as percentage (Deaths per 100 births)
    df['MortalityRate'] = (df['Deaths'] / df['Birth']) * 100

    return df


hand_df = get_handwashing_data()


# -----------------------------------------------------------------------------
# Draw the page

st.title(":soap: Handwashing & Childbed Fever — Clinic Mortality Explorer")

st.write(
    "This dashboard explores clinic birth/death data (mortality rates) over time."
)


# Controls
min_year = int(hand_df['Year'].min())
max_year = int(hand_df['Year'].max())

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_year,
    max_value=max_year,
    value=[min_year, max_year],
)

clinics = sorted(hand_df['Clinic'].unique())

selected_clinics = st.multiselect(
    'Which clinics would you like to view?',
    clinics,
    clinics,
)

if not selected_clinics:
    st.warning('Select at least one clinic to view the charts.')


# Filter data
filtered = hand_df[
    (hand_df['Clinic'].isin(selected_clinics))
    & (hand_df['Year'] >= from_year)
    & (hand_df['Year'] <= to_year)
]

st.header('Mortality rate over time')

if not filtered.empty:
    # Pivot so years are index and clinics are columns for easy plotting
    pivot = filtered.pivot_table(
        index='Year', columns='Clinic', values='MortalityRate'
    )

    st.line_chart(pivot)

    st.header(f'Metrics: {from_year} → {to_year}')

    cols = st.columns(4)

    for i, clinic in enumerate(selected_clinics):
        col = cols[i % len(cols)]
        with col:
            # Safely get first and last values (may be NaN)
            first_val = pivot.loc[from_year, clinic] if from_year in pivot.index and clinic in pivot.columns else np.nan
            last_val = pivot.loc[to_year, clinic] if to_year in pivot.index and clinic in pivot.columns else np.nan

            # Format display values
            if np.isnan(last_val):
                value_str = 'n/a'
            else:
                value_str = f"{last_val:.2f}%"

            if np.isnan(first_val) or np.isnan(last_val):
                delta = 'n/a'
                delta_color = 'off'
            else:
                # absolute percentage point change
                delta_val = last_val - first_val
                # also compute relative change if first_val != 0
                if first_val == 0:
                    delta = f"{delta_val:.2f}pp"
                else:
                    pct_change = (delta_val / first_val) * 100
                    delta = f"{pct_change:+.1f}%"
                delta_color = 'normal'

            st.metric(label=f"{clinic} mortality", value=value_str, delta=delta, delta_color=delta_color)

    st.header('Raw data')
    st.dataframe(filtered.sort_values(['Clinic', 'Year']).reset_index(drop=True))
else:
    st.info('No data available for the selected clinics / years.')
    
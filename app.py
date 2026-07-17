import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Flight Padding Analysis", page_icon="✈️", layout="wide")

st.title("✈️ Airport Congestion & Schedule Padding Analysis")
st.markdown("Investigating if airlines artificially pad their flight schedules to improve on-time performance metrics.")

# --- AIRPORT SELECTION ---
airport_selection = st.selectbox(
    "Select an Airport to Analyze:",
    options=["Chennai (MAA)", "Mumbai (BOM)"]
)

# Map the selection to the correct CSV file
if airport_selection == "Chennai (MAA)":
    csv_file = "data/flights_data_maa.csv"
else:
    csv_file = "data/flights_data_bom.csv"

# --- DATA LOADING ---
@st.cache_data(ttl=1)
def load_data(filepath):
    try:
        df = pd.read_csv(filepath)
        # Safely drop the origin_code column if it exists in historical data
        if 'origin_code' in df.columns:
            df = df.drop(columns=['origin_code'])
        return df
    except FileNotFoundError:
        # Just in case the file hasn't been generated yet
        return pd.DataFrame()

df = load_data(csv_file)

st.header(f"Live Data: {airport_selection}")

# Halt execution if no data is found yet
if df.empty:
    st.warning(f"No data found for {airport_selection} yet. Check your data folder or run the scraper first!")
    st.stop()

# --- METRICS CALCULATIONS ---
total_flights = len(df)
early_flights = len(df[df['classification'] == 'Early'])
average_delta = round(df['delta_minutes'].mean(), 1)

# --- UI: METRICS ROW ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total Flights Tracked", value=total_flights)
with col2:
    st.metric(label="Flights Arrived Early (>10 mins)", value=early_flights)
with col3:
    st.metric(label="Average Delta (Minutes)", value=average_delta)

st.divider()

# --- UI: RAW DATA TABLE ---
st.subheader("Raw Flight Records")
# Display the dataframe cleanly across the screen
st.dataframe(df, use_container_width=True)

st.divider()

# --- UI: VISUALIZATIONS ---
st.subheader("Arrival Classification Breakdown")

# 1. Overall Classification Chart (Upgraded to a colorful Donut Chart)
classification_counts = df['classification'].value_counts().reset_index()
classification_counts.columns = ['Classification', 'Flight Count']

# Assign specific colors (Green for Early, Blue for On-Time, Red for Late)
color_map = {'Early': '#00CC96', 'On-Time': '#636EFA', 'Late': '#EF553B', 'Cancelled': '#555555'}

fig1 = px.pie(
    classification_counts, 
    values='Flight Count', 
    names='Classification',
    color='Classification', 
    color_discrete_map=color_map,
    hole=0.4 # Makes it a donut chart!
)
# Update layout for a cleaner look
fig1.update_traces(textposition='inside', textinfo='percent+label')
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# 2. Airline Comparison Chart
st.subheader("Average Padding by Airline")
st.markdown("A negative number means the airline arrives early on average (potential schedule padding).")

# 1. Clean the data: drop rows with missing airlines and convert to string
df_clean = df.dropna(subset=['airline']).copy()
df_clean['airline'] = df_clean['airline'].astype(str).str.strip()

# 2. Group by airline and calculate the mean delta
airline_padding = df_clean.groupby('airline')['delta_minutes'].mean().reset_index()

# 3. Sort
airline_padding = airline_padding.sort_values(by='delta_minutes')

# 4. Create the chart
fig2 = px.bar(
    airline_padding, 
    x='airline', 
    y='delta_minutes', 
    color='delta_minutes',
    color_continuous_scale='RdBu',  # Red for late (positive), Blue for early (negative)
    text_auto='.1f', 
    labels={'airline': 'Airline', 'delta_minutes': 'Average Delta (mins)'}
)

fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, use_container_width=True)
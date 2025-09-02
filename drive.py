import streamlit as st
import pandas as pd
import re

st.title("📊 Google Sheet in Streamlit from Drive")

# Load IDs from secrets
sid = st.secrets["gdrive"]["spreadsheet_id"]
gid = st.secrets["gdrive"]["sheet_gid"]

# Build export URL for CSV format
url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"

st.write("Fetching data from the provided Google Sheet...")

# Read directly into a DataFrame
df = pd.read_csv(url)

# Display data
st.subheader("Sheet Preview")
st.dataframe(df.head())

# Display summary
st.subheader("Summary")
st.write(df.describe())

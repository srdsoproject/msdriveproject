import pandas as pd
import streamlit as st

url = st.secrets["onedrive"]["url"]

try:
    df = pd.read_excel(url)
    st.success("✅ File loaded successfully from OneDrive")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Could not load file: {e}")

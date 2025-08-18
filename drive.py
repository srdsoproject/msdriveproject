import pandas as pd
import streamlit as st

st.set_page_config(page_title="OneDrive Excel Loader")

url = st.secrets["onedrive"]["url"]

try:
    df = pd.read_excel(url)
    st.success("✅ Loaded successfully from OneDrive")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Could not load from OneDrive: {e}")

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import requests
import io

# ==================================================
# Helper functions for Google Drive Excel
# ==================================================

def download_excel_from_drive(file_id: str) -> pd.DataFrame:
    """Download Excel file from Google Drive (direct download link)."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_excel(io.BytesIO(response.content))

def upload_excel_to_drive(file_id: str, df: pd.DataFrame):
    """Overwrite Excel file in Google Drive (requires file to be shared with 'Editor' permission for your service account)."""
    url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}?uploadType=media"
    headers = {"Authorization": "Bearer dummy"}  # ⚠️ No token system yet, placeholder
    # For now, just save locally (since no auth is set up)
    df.to_excel("updated_database_file.xlsx", index=False)
    st.success("✅ Changes saved locally to updated_database_file.xlsx (Drive upload not enabled yet).")

# ==================================================
# Load Data
# ==================================================

file_id = st.secrets["gdrive"]["file_id"]

try:
    df = download_excel_from_drive(file_id)
except Exception as e:
    st.error(f"❌ Could not load file from Google Drive: {e}")
    st.stop()

st.markdown("### ✍️ Edit User Feedback/Remarks in Table")

if not df.empty:
    # Ensure stable IDs
    if "_original_sheet_index" not in df.columns:
        df["_original_sheet_index"] = df.index

    display_cols = [
        "Date of Inspection", "Type of Inspection", "Location", "Head", "Sub Head",
        "Deficiencies Noted", "Inspection By", "Action By", "Feedback",
        "User Feedback/Remark"
    ]
    editable_df = df[display_cols + ["_original_sheet_index"]].copy()

    # Format date
    if "Date of Inspection" in editable_df.columns:
        editable_df["Date of Inspection"] = pd.to_datetime(
            editable_df["Date of Inspection"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # AgGrid setup
    gb = GridOptionsBuilder.from_dataframe(editable_df)
    gb.configure_default_column(editable=False, wrapText=True, autoHeight=True)
    gb.configure_column(
        "User Feedback/Remark",
        editable=True,
        wrapText=True,
        autoHeight=True,
        cellEditor="agLargeTextCellEditor",
        cellEditorPopup=True,
        cellEditorParams={"maxLength": 4000, "rows": 10, "cols": 60}
    )
    gb.configure_column("_original_sheet_index", hide=True)
    gb.configure_grid_options(singleClickEdit=True)

    grid_response = AgGrid(
        editable_df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED,
        height=600,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True
    )

    edited_df = pd.DataFrame(grid_response["data"])

    if st.button("✅ Submit Feedback"):
        # Detect changes
        orig = df.set_index("_original_sheet_index")
        new = edited_df.set_index("_original_sheet_index")

        old_remarks = orig["User Feedback/Remark"].fillna("").astype(str)
        new_remarks = new["User Feedback/Remark"].fillna("").astype(str)

        common_ids = new_remarks.index.intersection(old_remarks.index)
        diff_mask = new_remarks.loc[common_ids] != old_remarks.loc[common_ids]
        changed_ids = diff_mask[diff_mask].index.tolist()

        if changed_ids:
            for oid in changed_ids:
                user_remark = new.loc[oid, "User Feedback/Remark"].strip()
                orig.at[oid, "Feedback"] = user_remark
                orig.at[oid, "User Feedback/Remark"] = ""

            # Reset index & save
            updated_df = orig.reset_index(drop=True)
            upload_excel_to_drive(file_id, updated_df)
            st.success(f"✅ Updated {len(changed_ids)} Feedback row(s).")
        else:
            st.info("ℹ️ No changes detected to save.")
else:
    st.info("Deficiencies will be updated soon!")

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
import streamlit as st
import os

st.set_page_config(layout="wide")
st.markdown("### ✍️ Edit User Feedback/Remarks in Table")

# -----------------------------------------------------
# GOOGLE SHEETS (read-only) LOGIC
# -----------------------------------------------------
def load_data():
    spreadsheet_id = st.secrets["gdrive"]["spreadsheet_id"]
    sheet_gid = st.secrets["gdrive"]["sheet_gid"]
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={sheet_gid}"
    return pd.read_csv(url)

def save_data(df):
    output = "local_copy.xlsx"
    df.to_excel(output, index=False)
    st.success(f"✅ Saved locally to {output} (Google Sheets write-back not enabled yet)")

# -----------------------------------------------------
# LOAD DATA INTO SESSION
# -----------------------------------------------------
if "df" not in st.session_state:
    st.session_state.df = load_data()

filtered = st.session_state.df.copy()

editable_filtered = filtered.copy()
if not editable_filtered.empty:
    # Add stable IDs for row tracking
    if "_original_sheet_index" not in editable_filtered.columns:
        editable_filtered["_original_sheet_index"] = editable_filtered.index
    if "_sheet_row" not in editable_filtered.columns:
        editable_filtered["_sheet_row"] = editable_filtered.index + 2

    display_cols = [
        "Date of Inspection", "Type of Inspection", "Location", "Head", "Sub Head",
        "Deficiencies Noted", "Inspection By", "Action By", "Feedback",
        "User Feedback/Remark"
    ]
    editable_df = editable_filtered[display_cols].copy()

    # Format date column
    if "Date of Inspection" in editable_df.columns:
        editable_df["Date of Inspection"] = pd.to_datetime(
            editable_df["Date of Inspection"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Add status column
    editable_df.insert(
        editable_df.columns.get_loc("User Feedback/Remark") + 1,
        "Status",
        ["🟢 OK" if pd.notna(r["Feedback"]) and str(r["Feedback"]).strip() != "" else "🔴 Pending"
         for _, r in editable_df.iterrows()]
    )

    # Add ID columns
    editable_df["_original_sheet_index"] = editable_filtered["_original_sheet_index"].values
    editable_df["_sheet_row"] = editable_filtered["_sheet_row"].values

    # --------- AG GRID CONFIG ---------
    gb = GridOptionsBuilder.from_dataframe(editable_df)
    gb.configure_default_column(editable=False, wrapText=True, autoHeight=True)

    gb.configure_column(
        "User Feedback/Remark",
        editable=True,
        cellEditor="agLargeTextCellEditor",
        cellEditorPopup=True,
        cellEditorParams={"maxLength": 4000, "rows": 10, "cols": 60}
    )
    gb.configure_column("_original_sheet_index", hide=True)
    gb.configure_column("_sheet_row", hide=True)
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

    # Buttons
    c1, c2, _ = st.columns([1, 1, 1])
    submitted = c1.button("✅ Submit Feedback")
    if c2.button("🔄 Refresh Data"):
        st.session_state.df = load_data()
        st.success("✅ Data refreshed successfully!")

    if submitted:
        orig = editable_filtered.set_index("_original_sheet_index")
        new = edited_df.set_index("_original_sheet_index")

        old_remarks = orig["User Feedback/Remark"].fillna("").astype(str)
        new_remarks = new["User Feedback/Remark"].fillna("").astype(str)

        common_ids = new_remarks.index.intersection(old_remarks.index)
        diff_mask = new_remarks.loc[common_ids] != old_remarks.loc[common_ids]
        changed_ids = diff_mask[diff_mask].index.tolist()

        if changed_ids:
            diffs = new.loc[changed_ids].copy()
            diffs["_sheet_row"] = orig.loc[changed_ids, "_sheet_row"].values

            for oid in changed_ids:
                user_remark = new.loc[oid, "User Feedback/Remark"].strip()
                if not user_remark:
                    continue
                # Move remark into Feedback
                diffs.at[oid, "Feedback"] = user_remark
                diffs.at[oid, "User Feedback/Remark"] = ""
                st.session_state.df.at[oid, "Feedback"] = user_remark
                st.session_state.df.at[oid, "User Feedback/Remark"] = ""

            # Save updated file locally
            save_data(st.session_state.df)
            st.success(f"✅ Updated {len(changed_ids)} Feedback row(s).")
        else:
            st.info("ℹ️ No changes detected to save.")
else:
    st.info("Deficiencies will be updated soon !")

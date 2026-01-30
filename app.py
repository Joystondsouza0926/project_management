import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import os

st.set_page_config(
    page_title="Product Opportunity Intake",
    layout="wide"
)

st.title("📥 Product Opportunity Intake Window")

# ---------------------------------------------------------
# 1. SESSION STATE INITIALIZATION
# ---------------------------------------------------------
DATA_FILE = "opportunities.csv"

if "df" not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.df = pd.read_csv(DATA_FILE)
        st.session_state.df["Opportunity ID"] = st.session_state.df["Opportunity ID"].astype(str)
    else:
        columns = [
            "Opportunity ID", "Title", "Source", "Target Setting",
            "Geography", "Urgency", "Priority", "Submission Date", "Status",
            "Submitted by", "Problem Statement", "Proposed Product",
            "Intended Use", "Comments"
        ]
        st.session_state.df = pd.DataFrame(columns=columns)

if "view_key" not in st.session_state:
    st.session_state.view_key = 0

# ---------------------------------------------------------
# 2. LEVEL 1 – SUMMARY LIST VIEW
# ---------------------------------------------------------
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

# Sync navigation with URL query parameters
if "opportunity_id" in st.query_params:
    query_id = st.query_params["opportunity_id"]
    if query_id in st.session_state.df["Opportunity ID"].values:
        st.session_state.selected_id = query_id
    else:
        st.session_state.selected_id = None
        st.query_params.clear()
else:
    st.session_state.selected_id = None

if st.session_state.selected_id is None:

    st.subheader("📊 Opportunity Summary")

    display_cols = [
        "Opportunity ID", "Title", "Source", "Target Setting",
        "Geography", "Urgency", "Priority", "Submission Date", "Status"
    ]

    # Prepare data for display
    df_display = st.session_state.df[display_cols].copy()

    # Format Opportunity ID as a link query
    df_display["Opportunity ID"] = df_display["Opportunity ID"].apply(
        lambda x: f"/?opportunity_id={x}"
    )

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Opportunity ID": st.column_config.LinkColumn(
                "Opportunity ID",
                display_text=r"opportunity_id=(.*)",
                help="Click to open details"
            ),
        },
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        st.write("")

    with col2:
        if st.button("➕ New Opportunity"):
            next_id = f"OP-2026-{len(st.session_state.df)+1:03d}"
            new_row = {
                "Opportunity ID": next_id,
                "Title": "",
                "Source": "R&D",
                "Target Setting": "",
                "Geography": "",
                "Urgency": "Low",
                "Priority": "P3",
                "Submission Date": datetime.today().strftime("%Y-%m-%d"),
                "Status": "Draft",
                "Submitted by": "",
                "Problem Statement": "",
                "Proposed Product": "",
                "Intended Use": "",
                "Comments": ""
            }
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame([new_row])],
                ignore_index=True
            )
            st.session_state.df.to_csv(DATA_FILE, index=False)
            st.session_state.selected_id = next_id
            st.query_params["opportunity_id"] = next_id
            st.rerun()

# ---------------------------------------------------------
# 3. LEVEL 2 – DETAILED DRILL-DOWN VIEW
# ---------------------------------------------------------
else:
    df = st.session_state.df
    idx = df[df["Opportunity ID"] == st.session_state.selected_id].index[0]

    # Header with Delete button aligned to the right
    t_col1, t_col2 = st.columns([5, 1])
    with t_col1:
        st.subheader(f"🧾 Detailed View — {st.session_state.selected_id}")
    with t_col2:
        if st.button("🗑️ Delete", help="Permanently delete this opportunity", use_container_width=True):
            st.session_state.df = st.session_state.df[st.session_state.df["Opportunity ID"] != st.session_state.selected_id]
            st.session_state.df.to_csv(DATA_FILE, index=False)
            st.session_state.selected_id = None
            st.query_params.clear()
            st.session_state.view_key += 1
            st.rerun()

    st.markdown("### Core Details")

    df.at[idx, "Title"] = st.text_input("Title *", df.at[idx, "Title"])

    source_options = ["Tender", "R&D", "Licensing", "Market Feedback", "Strategic Partner"]
    current_source = df.at[idx, "Source"]
    if current_source not in source_options:
        current_source = "R&D"

    df.at[idx, "Source"] = st.selectbox(
        "Source *",
        source_options,
        index=source_options.index(current_source)
    )

    target_options = ["Point of Care", "Lab", "Hospital", "Field"]
    current_target = df.at[idx, "Target Setting"]
    target_index = target_options.index(current_target) if current_target in target_options else 0

    df.at[idx, "Target Setting"] = st.selectbox(
        "Target Setting *",
        target_options,
        index=target_index
    )

    df.at[idx, "Geography"] = st.text_input("Geography *", df.at[idx, "Geography"])

    st.markdown("### Submission Details")

    df.at[idx, "Submitted by"] = st.text_input(
        "Submitted By *", df.at[idx, "Submitted by"]
    )

    df.at[idx, "Problem Statement"] = st.text_area(
        "Problem Statement *", df.at[idx, "Problem Statement"]
    )

    df.at[idx, "Proposed Product"] = st.text_area(
        "Proposed Product *", df.at[idx, "Proposed Product"]
    )

    df.at[idx, "Intended Use"] = st.text_area(
        "Intended Use *", df.at[idx, "Intended Use"]
    )

    df.at[idx, "Comments"] = st.text_area(
        "Expected Timeline Driver / Comments *", df.at[idx, "Comments"]
    )

    st.markdown("### Decision")

    decision = st.selectbox(
        "Decision",
        ["", "Accept", "Reject", "Park"]
    )

    col1, col2, col3 = st.columns(3)

    # ---------------------------------------------------------
    # 4. ACTION CONTROLS & LOGIC
    # ---------------------------------------------------------
    with col1:
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="💾 Download Draft (Excel)",
            data=output,
            file_name="product_opportunity_draft.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col2:
        if st.button(" Submit Decision"):
            # Validate required fields
            required_fields = {
                "Title": df.at[idx, "Title"],
                "Geography": df.at[idx, "Geography"],
                "Submitted By": df.at[idx, "Submitted by"],
                "Problem Statement": df.at[idx, "Problem Statement"],
                "Proposed Product": df.at[idx, "Proposed Product"],
                "Intended Use": df.at[idx, "Intended Use"],
                "Comments": df.at[idx, "Comments"]
            }
            missing = [k for k, v in required_fields.items() if not v or str(v).strip() == ""]

            if missing:
                st.error(f"Please fill in the following required fields: {', '.join(missing)}")
            elif decision == "Accept":
                df.at[idx, "Status"] = "Eligible for next PLM stage"
                st.success(
                    "Accepted ✅ — moved to Feasibility / Evaluation stage"
                )

            elif decision == "Reject":
                df.at[idx, "Status"] = "Rejected (Archived)"
                st.warning("Rejected ❌ — opportunity archived")

            elif decision == "Park":
                df.at[idx, "Status"] = "Inactive (Parked)"
                st.info("Parked ⏸ — opportunity set to inactive")

            else:
                st.error("Please select a decision")

    with col3:
        if st.button("⬅ Back to Dashboard"):
            st.session_state.selected_id = None
            st.query_params.clear()
            st.session_state.view_key += 1
            st.rerun()

    # Auto-save on any update in detailed view
    st.session_state.df.to_csv(DATA_FILE, index=False)

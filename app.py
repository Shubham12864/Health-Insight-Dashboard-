# app.py - Streamlit Frontend

import streamlit as st
import pandas as pd
import os
import numpy as np # Import numpy for NaN checking

# Import the backend logic
import backend_logic

# --- Page Configuration ---
st.set_page_config(page_title="Health Explorer", layout="wide")

# --- Initialize Session State --- 
# Use session state to store analysis results across reruns
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'wearable_results' not in st.session_state:
    st.session_state.wearable_results = {}
if 'medical_results' not in st.session_state:
    st.session_state.medical_results = {}
if 'plot_paths' not in st.session_state:
    st.session_state.plot_paths = {}
if 'error_message' not in st.session_state:
    st.session_state.error_message = None

# --- Main Application Structure ---
st.title("Personal Health Data & Medical Insight Explorer")

st.markdown("--- *Wearable Data Insights* ---")

# Wearable Data Summary Section
st.header("Wearable Data Summary (Last 7 Days)")
summary_cols = st.columns(4)
# Placeholders for metrics, will be updated after analysis runs
steps_avg_placeholder = summary_cols[0].empty()
hr_avg_placeholder = summary_cols[1].empty()
steps_high_placeholder = summary_cols[2].empty()
steps_low_placeholder = summary_cols[3].empty()

# Initialize placeholders with default values
steps_avg_placeholder.metric(label="Avg Steps", value="N/A")
hr_avg_placeholder.metric(label="Avg Heart Rate", value="N/A", help="Average of daily averages (bpm)")
steps_high_placeholder.metric(label="Highest Steps", value="N/A", help="Peak daily steps count")
steps_low_placeholder.metric(label="Lowest Steps", value="N/A", help="Lowest daily steps count")

# Wearable Data Trends Visualization Section
st.header("Wearable Data Trends")
plot_cols = st.columns(2)
# Placeholders for plots
with plot_cols[0]:
    st.subheader("Daily Steps")
    steps_plot_placeholder = st.empty()
    steps_plot_placeholder.write("Plot will appear here after analysis.")
with plot_cols[1]:
    st.subheader("Daily Average Heart Rate")
    hr_plot_placeholder = st.empty()
    hr_plot_placeholder.write("Plot will appear here after analysis.")

st.markdown("--- *Medical Report Analysis* ---")

# Medical Report Analysis Section
st.header("Medical Report Analysis")
# Placeholder for medical report results table
medical_results_placeholder = st.empty()
medical_results_placeholder.write("Analysis results will appear here.")

st.markdown("--- *Controls & Information* ---")

# Run Analysis Button
if st.button("Run Analysis"):
    # Clear previous error messages
    st.session_state.error_message = None
    st.session_state.analysis_complete = False # Reset flag while running
    with st.spinner("Running analysis... Please wait."): # Show spinner during execution
        try:
            # Call the backend function to perform the analysis
            wearable_res, medical_res, plots, error = backend_logic.run_complete_analysis()

            # Store results in session state
            st.session_state.wearable_results = wearable_res
            st.session_state.medical_results = medical_res
            st.session_state.plot_paths = plots
            st.session_state.error_message = error
            st.session_state.analysis_complete = True # Set flag to indicate completion

        except Exception as e:
            # Catch any unexpected errors during backend execution
            st.session_state.error_message = f"An unexpected error occurred: {e}"
            st.session_state.analysis_complete = False # Ensure flag is false on error
            # Clear results on unexpected error
            st.session_state.wearable_results = {}
            st.session_state.medical_results = {}
            st.session_state.plot_paths = {}

    # After the button logic, Streamlit reruns the script.
    # The UI update logic below will use the new session state.
    # Add a success message if no error occurred
    if st.session_state.analysis_complete and not st.session_state.error_message:
        st.success("Analysis complete!")
    elif st.session_state.error_message:
         st.error(f"Analysis failed: {st.session_state.error_message}")

# Display Error Message if any (this catches errors stored in session state)
# Only show if analysis is not complete OR if it completed with an error
if not st.session_state.analysis_complete and st.session_state.error_message:
    st.error(f"Analysis Error: {st.session_state.error_message}")

# --- UI Update Logic (Based on Session State) ---
# This section updates the UI elements based on data stored in session_state

if st.session_state.analysis_complete:
    # Update Wearable Summary Metrics
    wearable_res = st.session_state.wearable_results
    if wearable_res:
        # Safely get 7-day averages
        avg_df = wearable_res.get("7_day_averages")
        # Check if avg_df is a DataFrame and not empty
        if isinstance(avg_df, pd.DataFrame) and not avg_df.empty:
            latest_avg_steps = avg_df["Steps_7DayAvg"].iloc[-1]
            latest_avg_hr = avg_df["HeartRate_7DayAvg"].iloc[-1]
            # Check for NaN before formatting
            steps_avg_val = f"{latest_avg_steps:.0f}" if pd.notna(latest_avg_steps) else "N/A"
            hr_avg_val = f"{latest_avg_hr:.1f}" if pd.notna(latest_avg_hr) else "N/A"
            steps_avg_placeholder.metric(label="Avg Steps", value=steps_avg_val)
            hr_avg_placeholder.metric(label="Avg Heart Rate", value=hr_avg_val, help="Average of daily averages (bpm)")
        else:
            steps_avg_placeholder.metric(label="Avg Steps", value="N/A")
            hr_avg_placeholder.metric(label="Avg Heart Rate", value="N/A", help="Average of daily averages (bpm)")

        # Safely get step extremes
        date_max, max_steps, date_min, min_steps = wearable_res.get("step_extremes", (None, None, None, None))
        if max_steps is not None and pd.notna(max_steps) and date_max is not None:
            steps_high_placeholder.metric(label="Highest Steps", value=f"{max_steps:.0f}", help=f"On {date_max.strftime('%Y-%m-%d')}")
        else:
            steps_high_placeholder.metric(label="Highest Steps", value="N/A")
        if min_steps is not None and pd.notna(min_steps) and date_min is not None:
            steps_low_placeholder.metric(label="Lowest Steps", value=f"{min_steps:.0f}", help=f"On {date_min.strftime('%Y-%m-%d')}")
        else:
            steps_low_placeholder.metric(label="Lowest Steps", value="N/A")
    else:
        # Handle case where wearable analysis results are empty/missing after successful run
        steps_avg_placeholder.metric(label="Avg Steps", value="N/A")
        hr_avg_placeholder.metric(label="Avg Heart Rate", value="N/A", help="Average of daily averages (bpm)")
        steps_high_placeholder.metric(label="Highest Steps", value="N/A")
        steps_low_placeholder.metric(label="Lowest Steps", value="N/A")

    # Update Medical Report Analysis Table
    medical_res = st.session_state.medical_results
    if medical_res:
        # Convert the results dict to a DataFrame for better display
        report_items = []
        for label, data in medical_res.items():
            report_items.append({
                "Metric": label,
                "Value": data.get("value", "N/A"),
                "Status": data.get("flag", "N/A"),
                "Normal Range": str(data.get("normal_range", "N/A"))
            })
        if report_items:
            report_df = pd.DataFrame(report_items)
            # Use st.dataframe to display the table
            medical_results_placeholder.dataframe(report_df, use_container_width=True)
        else:
             medical_results_placeholder.write("No medical metrics found in the report analysis.")
    else:
        # Handle case where medical analysis results are empty/missing after successful run
        medical_results_placeholder.write("No medical report analysis results available.")

    # Update Plots
    plot_paths = st.session_state.plot_paths
    if plot_paths:
        steps_plot_path = plot_paths.get('steps')
        hr_plot_path = plot_paths.get('hr')

        # Display Steps Plot
        if steps_plot_path and os.path.exists(steps_plot_path):
            steps_plot_placeholder.image(steps_plot_path, use_column_width=True)
        else:
            steps_plot_placeholder.warning("Steps plot image not found.")

        # Display Heart Rate Plot
        if hr_plot_path and os.path.exists(hr_plot_path):
            hr_plot_placeholder.image(hr_plot_path, use_column_width=True)
        else:
            hr_plot_placeholder.warning("Heart rate plot image not found.")
    else:
        # Handle case where plot paths are missing after successful run
        steps_plot_placeholder.warning("Steps plot data unavailable.")
        hr_plot_placeholder.warning("Heart rate plot data unavailable.")

else:
    # If analysis hasn't been run or failed unexpectedly, ensure placeholders show default state
    steps_avg_placeholder.metric(label="Avg Steps", value="N/A")
    hr_avg_placeholder.metric(label="Avg Heart Rate", value="N/A", help="Average of daily averages (bpm)")
    steps_high_placeholder.metric(label="Highest Steps", value="N/A")
    steps_low_placeholder.metric(label="Lowest Steps", value="N/A")
    steps_plot_placeholder.write("Plot will appear here after analysis.")
    hr_plot_placeholder.write("Plot will appear here after analysis.")
    medical_results_placeholder.write("Analysis results will appear here.")


# Disclaimer (always visible at the bottom)
st.warning("**Disclaimer:** This tool is for informational and educational purposes only and does not constitute medical advice. Consult with a qualified healthcare professional for any health concerns.")

# --- End of Structure ---


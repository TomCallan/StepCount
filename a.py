import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import requests

key = st.secrets["key"]

bin = "https://api.jsonbin.io/v3/b/" + "666cbdf9ad19ca34f8792107"

headers = {
    "X-Master-Key": key,
    "Content-Type": "application/json"
}

r = requests.get(bin + "/latest", headers=headers)
data = r.json()
print(data)

# Load existing data from the file if it exists
if 'contributions' not in st.session_state:
    if len(data) > 1:
        st.session_state.contributions = data['record']
        st.session_state.counter = sum(entry['number'] for entry in st.session_state.contributions)
    else:
        st.session_state.contributions = []
        st.session_state.counter = 0

# Title of the app
st.title("Counter App")

# Your min and max values
min_val = 0
max_val = 10000 * 30 * 5  # 100 iterations for simplicity

# Create a placeholder for the progress bar and text
progress_bar = st.empty()
progress_text = st.empty()

# Calculate the percentage for the progress bar
percentage = st.session_state.counter / max_val * 100 if max_val != 0 else 0

# Update the progress bar with the current percentage
progress_bar.progress(percentage / 100)

# Update the text under the progress bar to show min, current, and max values
progress_style = f"""
<div style="
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: relative;">
    <span>0</span>
    <div style="
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
    ">{round(percentage, 2)}%</div>
    <span>{max_val}</span>
</div>
"""
progress_text.markdown(progress_style, unsafe_allow_html=True)

# Display the current counter value
st.write(f"Current Counter Value: {st.session_state.counter}")

# Input fields for name and number
name = st.text_input("Enter your name")
number = st.number_input("Enter a number", step=1)

# Layout for Add to Counter and Download Data buttons
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("Add to Counter"):
        if name:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            contribution = {'name': name, 'number': number, 'timestamp': timestamp, 'active': True}
            st.session_state.contributions.append(contribution)
            st.session_state.counter += number
            req = requests.put(bin, headers=headers, json=st.session_state.contributions)
            st.experimental_rerun()
        else:
            st.error("Please enter your name")

# Function to convert DataFrame to CSV
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

with col3:
    if st.session_state.contributions:
        csv = convert_df_to_csv(pd.DataFrame(st.session_state.contributions))
        st.download_button(label="Download Data", data=csv, file_name='contributions.csv', mime='text/csv')

# Display contributions in a table-like format
if st.session_state.contributions:
    st.write("Contributions:")
    df = pd.DataFrame(st.session_state.contributions)
    df = df.sort_values(by='timestamp', ascending=False)
    
    # Create columns
    colms = st.columns((1, 2, 2, 2, 1))
    fields = ["№", 'Name', 'Number', 'Timestamp', "Action"]
    for col, field_name in zip(colms, fields):
        col.write(f"**{field_name}**")

    # Display data rows with an "X" button for each
    for x, row in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns((1, 2, 2, 2, 1))
        col1.write(x)
        col2.write(row['name'])
        col3.write(row['number'])
        col4.write(row['timestamp'])
        
        disable_status = row['active']  # flexible type of button
        button_type = "Delete" if disable_status else ""
        button_phold = col5.empty()  # create a placeholder
        do_action = button_phold.button(button_type, key=x)
        if do_action & disable_status:
            st.session_state.counter -= row['number']
            st.session_state.contributions = [entry for i, entry in enumerate(st.session_state.contributions) if i != x]
            req = requests.put(bin, headers=headers, json=st.session_state.contributions)
            st.experimental_rerun()
            button_phold.empty()  # remove button
import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import requests

key = st.secrets["key"]

bin = "https://api.jsonbin.io/v3/b/"+"666cbdf9ad19ca34f8792107"

headers = {
    "X-Master-Key": key,
    "Content-Type": "application/json"
}

r = requests.get(bin+"/latest", headers=headers)
data = r.json()

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

# Input fields for name and number
name = st.text_input("Enter your name")
number = st.number_input("Enter a number", step=1)

# Button to add the number to the counter
if st.button("Add to Counter"):
    if name:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        contribution = {'name': name, 'number': number, 'timestamp': timestamp}
        st.session_state.contributions.append(contribution)
        st.session_state.counter += number
        req = requests.put(bin, json=st.session_state.contributions, headers=headers)
        st.experimental_rerun()
    else:
        st.error("Please enter your name")

# Display the current counter value
st.write(f"Current Counter Value: {st.session_state.counter}")

# Display contributions in a table-like format with search, sort, and filter
if st.session_state.contributions:
    st.write("Contributions:")
    df = pd.DataFrame(st.session_state.contributions)
    df = df.sort_values(by='timestamp', ascending=False)

    # Define a custom renderer for the delete button
    cell_renderer = JsCode('''
    function(params) {
        return `<button onclick="deleteRow('${params.data.timestamp}')">X</button>`;
    }
    ''')

    # Add the custom renderer to the grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column('Action', headerName='Action', cellRenderer=cell_renderer)
    gb.configure_default_column(editable=True, sortable=True, filter=True)
    gb.configure_selection('single')
    grid_options = gb.build()

    # Include the delete button
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        theme='streamlit'
    )

    # Handle row deletion
    selected_rows = grid_response['selected_rows']
    if selected_rows:
        selected_row = selected_rows[0]
        if 'Action' in selected_row:
            selected_index = df[df['timestamp'] == selected_row['timestamp']].index[0]
            st.session_state.counter -= df.at[selected_index, 'number']
            st.session_state.contributions.pop(selected_index)
            req = requests.put(bin, json=st.session_state.contributions, headers=headers)
            st.experimental_rerun()

    # Include the JavaScript function for row deletion
    st.markdown('''
    <script>
    function deleteRow(timestamp) {
        const streamlitDoc = window.parent.document;
        const button = Array.from(
            streamlitDoc.querySelectorAll('button[data-baseweb="button"]')
        ).find(el => el.textContent === 'Remove Selected Entry');
        if (button) {
            button.click();
        }
    }
    </script>
    ''', unsafe_allow_html=True)

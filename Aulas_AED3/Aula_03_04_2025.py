import streamlit as st

def visualArray(value):

# Function to create a row of widgets (with row number input to assure unique keys)

  # columns to lay out the inputs
   grid = st.columns(value)
   # Loop to create rows of input widgets
   for i in range(num_rows):
        with grid[i]:
            st.text_input('col{i+1}', key=f'input_col1{row}')
    

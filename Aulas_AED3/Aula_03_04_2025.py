import streamlit as st
'''
vetor=[0]*13

grid =st.columns(13)
with grid[0]:
    st.text_input("pos ", value=vetor [0], max_chars=1,disabled=False)
with grid[1]:
    st.text_input("pos ", value=vetor [1], max_chars=1,disabled=False)


'''
def visualArray(value):
# Function to create a row of widgets (with row number input to assure unique keys)
   vetor = ["empty"]*value;
   # columns to lay out the inputs
   grid = st.columns(value)
   # Loop to create rows of input widgets
   for i in range(value):
        with grid[i]:
            st.text_input("pos {int(i)}", value=vetor [i], max_chars=1,disabled=False)
st.title("Aula de 03-04-2025")
visualArray(13)


import streamlit as st

vetor=[""]
def visualArray(value):
    vetor=["0"]*value
    grid =st.columns(value)
    for i in range(value):
        with grid[i]:
            st.text_input(f"pos {i}", value=vetor [i], key=i,max_chars=1,disabled=False)
    return grid
st.title("Aula de 03-04-2025")

columns_set=visualArray(13)



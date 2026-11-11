import streamlit as st

api_key = st.secrets["tmdb_api_key"]

st.title("The Fossick Finder")
st.write("My TMDB API key loaded successfully!")
import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="The Fossick Finder", page_icon="🎬", layout="wide")

# 2. Load API Key from Secrets
try:
    api_key = st.secrets["tmdb_api_key"]
except Exception:
    st.error("TMDB API key not found in Streamlit Secrets. Please check your app settings.")
    st.stop()

st.title("🎬 The Fossick Finder")
st.write("Search for your favorite movies using TMDB data!")

# 3. Search Bar Input
search_query = st.text_input("Enter a movie title:", "")

if search_query:
    # 4. Query TMDB API
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={search_query}"
    
    with st.spinner("Searching TMDB..."):
        response = requests.get(url)
        
    if response.status_code == 200:
        data = response.json()
        movies = data.get("results", [])
        
        if movies:
            st.success(f"Found {len(movies)} results for '{search_query}':")
            
            # 5. Display Movies in a Grid
            for movie in movies[:5]:  # Show top 5 results
                col1, col2 = st.columns([1, 3])
                
                poster_path = movie.get("poster_path")
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                
                with col1:
                    if poster_url:
                        st.image(poster_url, width=150)
                    else:
                        st.write("No poster available")
                        
                with col2:
                    st.subheader(movie.get("title", "Unknown Title"))
                    st.write(f"**Release Date:** {movie.get('release_date', 'N/A')}")
                    st.write(f"**Rating:** {movie.get('vote_average', 'N/A')} / 10")
                    st.write(movie.get("overview", "No description available."))
                st.divider()
        else:
            st.warning("No movies found matching that title. Try another search!")
    else:
        st.error("Failed to connect to TMDB API. Please check your connection or API key.")
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
st.write("Explore and discover movies by genre, popularity, and preferences using TMDB Discover!")

# TMDB Genre ID Mapping Dictionary
GENRES = {
    "All Genres": None,
    "Action": 28,
    "Adventure": 12,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Family": 10751,
    "Fantasy": 14,
    "History": 36,
    "Horror": 27,
    "Music": 10402,
    "Mystery": 9648,
    "Romance": 10749,
    "Science Fiction": 878,
    "Thriller": 53,
    "War": 10752,
    "Western": 37
}

# 3. Sidebar Filters for Discover Mode
st.sidebar.header("🔍 Discover Filters")
selected_genre_name = st.sidebar.selectbox("Select Genre", list(GENRES.keys()))
exclude_animation = st.sidebar.toggle("Exclude Cartoons / Animation", value=False)

# 4. Discover Button Trigger
if st.sidebar.button("Discover Movies", type="primary"):
    genre_id = GENRES[selected_genre_name]
    
    # Build TMDB Discover URL
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&sort_by=popularity.desc"
    
    # Add Genre filter if selected
    if genre_id:
        url += f"&with_genres={genre_id}"
        
    # Add Animation exclusion if toggled (and user didn't explicitly select Animation)
    if exclude_animation and genre_id != 16:
        url += "&without_genres=16"
        
    with st.spinner("Discovering movies..."):
        response = requests.get(url)
        
    if response.status_code == 200:
        data = response.json()
        movies = data.get("results", [])
        
        if movies:
            st.success(f"Found {len(movies)} popular movies matching your filters:")
            
            # Display Movies in a Grid (Top 10 results)
            for movie in movies[:10]:
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
            st.warning("No movies found matching those filters. Try adjusting your options!")
    else:
        st.error("Failed to connect to TMDB API. Please check your connection or API key.")
else:
    st.info("👈 Use the sidebar filters on the left and click **Discover Movies** to start exploring!")
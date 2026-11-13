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
st.write("Explore movies and TV series by genre, media type, and emotional tone!")

# Genre Dictionaries for Movies and TV Shows
MOVIE_GENRES = {
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

TV_GENRES = {
    "All Genres": None,
    "Action & Adventure": 10759,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Family": 10751,
    "Kids": 10762,
    "Mystery": 9648,
    "Reality": 10764,
    "Sci-Fi & Fantasy": 10765,
    "Soap": 10766,
    "Talk": 10767,
    "War & Politics": 10768,
    "Western": 37
}

# Tone & Vibe Mapping (Maps to TMDB Keyword IDs or sort modifiers)
VIBES = {
    "Any Vibe": None,
    "Fun & Uplifting (Feel-Good)": {"keyword": "9799", "sort": "vote_average.desc"},      # upbeat / feel-good
    "Serious & Thought-Provoking": {"keyword": "1563", "sort": "vote_average.desc"},      # philosophy / drama
    "Dark & Gritty": {"keyword": "10986", "sort": "popularity.desc"},                    # dark / gritty
    "Light & Quirky / Offbeat": {"keyword": "10287", "sort": "popularity.desc"},         # quirky / eccentric
    "Action-Packed / High Energy": {"keyword": "9715", "sort": "popularity.desc"}         # chase / action
}

# 3. Sidebar Controls
st.sidebar.header("🔍 Discover Filters")
media_type = st.sidebar.radio("Select Media Type", ["Movies", "TV Shows"])

if media_type == "Movies":
    genre_dict = MOVIE_GENRES
    endpoint = "movie"
else:
    genre_dict = TV_GENRES
    endpoint = "tv"

selected_genre_name = st.sidebar.selectbox("Select Genre", list(genre_dict.keys()))
selected_vibe_name = st.sidebar.selectbox("Select Tone / Vibe", list(VIBES.keys()))
exclude_animation = st.sidebar.toggle("Exclude Cartoons / Animation", value=False)

# 4. Discover Button Trigger
if st.sidebar.button("Discover", type="primary"):
    genre_id = genre_dict[selected_genre_name]
    vibe_data = VIBES[selected_vibe_name]
    
    # Determine sorting based on vibe preference
    sort_by = vibe_data["sort"] if vibe_data else "popularity.desc"
    
    # Build TMDB Discover URL
    url = f"https://api.themoviedb.org/3/discover/{endpoint}?api_key={api_key}&sort_by={sort_by}"
    
    # Add Genre filter if selected
    if genre_id:
        url += f"&with_genres={genre_id}"
        
    # Add Vibe / Keyword filter if selected
    if vibe_data and vibe_data["keyword"]:
        url += f"&with_keywords={vibe_data['keyword']}"
        
    # Add Animation exclusion if toggled
    if exclude_animation and genre_id != 16:
        url += "&without_genres=16"
        
    with st.spinner(f"Discovering {media_type.lower()} matching your vibe..."):
        response = requests.get(url)
        
    if response.status_code == 200:
        data = response.json()
        items = data.get("results", [])
        
        if items:
            st.success(f"Found {len(items)} {media_type.lower()} matching your criteria:")
            
            # Display Results Grid (Top 10)
            for item in items[:10]:
                col1, col2 = st.columns([1, 3])
                
                poster_path = item.get("poster_path")
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                
                title = item.get("title") or item.get("name", "Unknown Title")
                date_key = "release_date" if endpoint == "movie" else "first_air_date"
                date_val = item.get(date_key, 'N/A')
                
                with col1:
                    if poster_url:
                        st.image(poster_url, width=150)
                    else:
                        st.write("No poster available")
                        
                with col2:
                    st.subheader(title)
                    st.write(f"**First Air / Release Date:** {date_val}")
                    st.write(f"**Rating:** {item.get('vote_average', 'N/A')} / 10")
                    st.write(item.get("overview", "No description available."))
                st.divider()
        else:
            st.warning(f"No {media_type.lower()} found matching that exact vibe/genre combination. Try broadening your options!")
    else:
        st.error("Failed to connect to TMDB API. Please check your connection or API key.")
else:
    st.info(f"👈 Use the sidebar to pick your media type, genre, and **Tone & Vibe**, then click **Discover**!")
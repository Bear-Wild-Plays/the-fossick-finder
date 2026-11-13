import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="The Fossick Finder", page_icon="🎬", layout="wide")

# 2. Load API Keys from Secrets
try:
    api_key = st.secrets["tmdb_api_key"]
    omdb_api_key = st.secrets["omdb_api_key"]
except Exception:
    st.error("API keys not found in Streamlit Secrets. Please ensure both 'tmdb_api_key' and 'omdb_api_key' are added.")
    st.stop()

st.title("🎬 The Fossick Finder")
st.write("Explore movies and TV series with multi-database intelligence: TMDB discovery + OMDb ratings & reviews!")

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

# Tone & Vibe Mapping
VIBES = {
    "Any Vibe": None,
    "Fun & Uplifting (Feel-Good)": {"keyword": "9799", "sort": "vote_average.desc"},
    "Serious & Thought-Provoking": {"keyword": "1563", "sort": "vote_average.desc"},
    "Dark & Gritty": {"keyword": "10986", "sort": "popularity.desc"},
    "Light & Quirky / Offbeat": {"keyword": "10287", "sort": "popularity.desc"},
    "Action-Packed / High Energy": {"keyword": "9715", "sort": "popularity.desc"}
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

st.sidebar.subheader("✨ Advanced Filters")
exclude_animation = st.sidebar.toggle("Exclude Cartoons / Animation", value=False)
black_and_white = st.sidebar.toggle("Black & White Only", value=False)
blurb_keyword = st.sidebar.text_input("Search inside blurb / overview", "", placeholder="e.g. space, island, NYC")

# 4. Discover Button Trigger
if st.sidebar.button("Discover", type="primary"):
    genre_id = genre_dict[selected_genre_name]
    vibe_data = VIBES[selected_vibe_name]
    
    sort_by = vibe_data["sort"] if vibe_data else "popularity.desc"
    
    url = f"https://api.themoviedb.org/3/discover/{endpoint}?api_key={api_key}&sort_by={sort_by}"
    
    if genre_id:
        url += f"&with_genres={genre_id}"
        
    keyword_list = []
    if vibe_data and vibe_data["keyword"]:
        keyword_list.append(vibe_data["keyword"])
    if black_and_white:
        keyword_list.append("10183")
        
    if keyword_list:
        url += f"&with_keywords={'|'.join(keyword_list)}"
        
    if exclude_animation and genre_id != 16:
        url += "&without_genres=16"
        
    with st.spinner(f"Discovering {media_type.lower()} across databases..."):
        response = requests.get(url)
        
    if response.status_code == 200:
        data = response.json()
        items = data.get("results", [])
        
        if blurb_keyword:
            keyword_lower = blurb_keyword.lower()
            items = [item for item in items if keyword_lower in item.get("overview", "").lower()]
        
        if items:
            st.success(f"Found {len(items)} {media_type.lower()} matching your criteria:")
            
            for item in items[:10]:
                col1, col2 = st.columns([1, 3])
                
                poster_path = item.get("poster_path")
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                
                title = item.get("title") or item.get("name", "Unknown Title")
                date_key = "release_date" if endpoint == "movie" else "first_air_date"
                date_val = item.get(date_key, 'N/A')
                release_year = date_val.split("-")[0] if date_val != 'N/A' else ""
                tmdb_rating = item.get('vote_average', 5.0)
                
                # Fetch cross-database ratings from OMDb API
                omdb_rating = "N/A"
                rt_rating = "N/A"
                metacritic = "N/A"
                
                try:
                    omdb_url = f"http://www.omdbapi.com/?apikey={omdb_api_key}&t={requests.utils.quote(title)}"
                    if release_year:
                        omdb_url += f"&y={release_year}"
                    omdb_res = requests.get(omdb_url).json()
                    
                    if omdb_res.get("Response") == "True":
                        omdb_rating = omdb_res.get("imdbRating", "N/A")
                        metacritic = omdb_res.get("Metascore", "N/A")
                        for r in omdb_res.get("Ratings", []):
                            if r.get("Source") == "Rotten Tomatoes":
                                rt_rating = r.get("Value")
                except Exception:
                    pass  # Fallback gracefully if OMDb network call fails
                
                # Custom Cheesiness Calculation Formula
                cheesiness_score = max(1, min(10, int((10 - tmdb_rating) * 1.2 + 2)))
                if cheesiness_score >= 8:
                    cheese_badge = "🧀 Super Cheesy / Cult Classic"
                elif cheesiness_score >= 5:
                    cheese_badge = "🍿 Mildly Cheesy / Fun Camp"
                else:
                    cheese_badge = "🎭 Serious / Prestigious"
                
                with col1:
                    if poster_url:
                        st.image(poster_url, width=150)
                    else:
                        st.write("No poster available")
                        
                with col2:
                    st.subheader(title)
                    st.write(f"**Release / Air Date:** {date_val}")
                    st.write(f"**Ratings:** TMDB: {tmdb_rating}/10 | IMDb: {omdb_rating} | Rotten Tomatoes: {rt_rating} | Metacritic: {metacritic}")
                    st.write(f"**Cheesiness Meter:** {cheesiness_score}/10 ({cheese_badge})")
                    st.write(item.get("overview", "No description available."))
                st.divider()
        else:
            st.warning(f"No {media_type.lower()} found matching those filters and blurb search keyword. Try broadening your terms!")
    else:
        st.error("Failed to connect to TMDB API. Please check your connection or API key.")
else:
    st.info(f"👈 Use the sidebar to configure your multi-database filters and click **Discover**!")
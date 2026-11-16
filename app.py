import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="The Fossick Finder", page_icon="⛏️", layout="wide")

# Custom CSS for Western Gold Rush Theme & Monument Valley Banner
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rye&display=swap');
    
    /* Main background - Deep Rich Soil */
    .stApp {
        background-color: #1C1713;
        color: #F4EFE6;
    }
    
    /* Sidebar background - Dark Earth / Sandstone */
    [data-testid="stSidebar"] {
        background-color: #29221C;
        border-right: 2px solid #5C4938;
    }
    
    /* Western Font for Titles & Headers */
    h1, h2, h3 {
        font-family: 'Rye', serif !important;
        color: #E5B84B !important;
    }
    
    /* Monument Valley Banner Container */
    .banner-container {
        background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center;
        border-radius: 12px;
        padding: 45px 25px;
        text-align: center;
        margin-bottom: 25px;
        border: 2px solid #6E5641;
        box-shadow: 0 8px 20px rgba(0,0,0,0.6);
    }
    
    /* Primary Action Button - Gold Nugget Style */
    div.stButton > button[kind="primary"] {
        background-color: #D4AF37;
        color: #1C1713;
        font-weight: bold;
        border: 2px solid #F3E5AB;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #F3E5AB;
        color: #1C1713;
        border-color: #D4AF37;
        transform: scale(1.02);
    }
    
    /* Movie Result Card Styling - Excavated Stone & Gem Border */
    .gem-card {
        background-color: #261F1A;
        border: 1px solid #6E5641;
        border-left: 5px solid #38BDF8;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
    }
    
    /* Dividers - Earthy Copper/Bronze */
    hr {
        border-color: #5C4938;
    }
</style>
""", unsafe_allow_html=True)

# 2. Load API Keys from Secrets
try:
    api_key = st.secrets["tmdb_api_key"]
    omdb_api_key = st.secrets["omdb_api_key"]
except Exception:
    st.error("API keys not found in Streamlit Secrets. Please ensure both 'tmdb_api_key' and 'omdb_api_key' are added.")
    st.stop()

# Custom Banner Section with New Text
st.markdown("""
<div class="banner-container">
    <h1 style="color: #F4EFE6; margin-bottom: 15px; text-shadow: 3px 3px 6px rgba(0,0,0,0.9); font-family: 'Rye', serif;">The Fossick Finder</h1>
    <p style="color: #FDF6E2; font-size: 1.25rem; font-family: 'Georgia', serif; font-style: italic; max-width: 850px; margin: 0 auto; text-shadow: 2px 2px 4px rgba(0,0,0,0.9);">
        Instead of scrolling to find the latest release, get your hands dirty and dig through cinema and television history to find a gem that is right for tonight.
    </p>
</div>
""", unsafe_allow_html=True)

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

# 3. Sidebar Controls (The Prospector's Toolkit)
st.sidebar.header("⛏️ Prospecting Tools")
media_type = st.sidebar.radio("Where are we digging?", ["Movies", "TV Shows"])

if media_type == "Movies":
    genre_dict = MOVIE_GENRES
    endpoint = "movie"
else:
    genre_dict = TV_GENRES
    endpoint = "tv"

selected_genre_name = st.sidebar.selectbox("Choose Your Vein (Genre)", list(genre_dict.keys()))
selected_vibe_name = st.sidebar.selectbox("Select Atmosphere / Tone", list(VIBES.keys()))

st.sidebar.subheader("Prospecting Pans")
exclude_animation = st.sidebar.toggle("Filter out Cartoons / Animation", value=False)
black_and_white = st.sidebar.toggle("Classic Black & White Only", value=False)
blurb_keyword = st.sidebar.text_input("Sift plot blurbs for a word", "", placeholder="e.g. gold, space, island")

# 4. Discover Button Trigger
if st.sidebar.button("⛏️ Dig for Gems!", type="primary"):
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
        
    with st.spinner(f"⛏️ Digging through the dirt and gravel for {media_type.lower()}..."):
        response = requests.get(url)
        
    if response.status_code == 200:
        data = response.json()
        items = data.get("results", [])
        
        if blurb_keyword:
            keyword_lower = blurb_keyword.lower()
            items = [item for item in items if keyword_lower in item.get("overview", "").lower()]
        
        if items:
            st.success(f"💎 Strike! Unearthed {len(items)} {media_type.lower()} from the quarry:")
            
            for item in items[:10]:
                st.markdown('<div class="gem-card">', unsafe_allow_html=True)
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
                    pass
                
                # Custom Cheesiness Calculation Formula
                cheesiness_score = max(1, min(10, int((10 - tmdb_rating) * 1.2 + 2)))
                if cheesiness_score >= 8:
                    cheese_badge = "🧀 Fool's Gold / Super Cheesy Cult Classic"
                elif cheesiness_score >= 5:
                    cheese_badge = "🍿 Rough Cut / Mildly Cheesy Fun"
                else:
                    cheese_badge = "💎 Flawless Cut / Prestigious"
                
                with col1:
                    if poster_url:
                        st.image(poster_url, width=150)
                    else:
                        st.write("🪨 No poster unearthed")
                        
                with col2:
                    st.subheader(f"💎 {title}")
                    st.write(f"**Unearthed (Release / Air Date):** {date_val}")
                    st.write(f"**Appraisal:** TMDB: `{tmdb_rating}/10` | IMDb: `{omdb_rating}` | Rotten Tomatoes: `{rt_rating}` | Metacritic: `{metacritic}`")
                    st.write(f"**Purity & Cheese:** `{cheesiness_score}/10` — {cheese_badge}")
                    st.write(item.get("overview", "No plot inscription found."))
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning(f"🪨 Nothing but gravel! No {media_type.lower()} matched those exact filters. Try digging in a broader vein!")
    else:
        st.error("💥 Cave-in! Failed to connect to TMDB API. Please check your connection or API key.")
else:
    st.info("👈 Grab your **Prospecting Tools** on the left, set your filters, and click **⛏️ Dig for Gems!** to start mining.")
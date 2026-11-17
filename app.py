import streamlit as st
import requests
import json
from google import genai
from prompts.prospector_prompts import build_curation_prompt, PROMPT_VERSION

# 1. Page Configuration
st.set_page_config(page_title="The Fossick Finder", page_icon="⛏️", layout="wide")

# Custom CSS for Western Gold Rush Theme, Desert Canyon Banner, & Earthy Soil Background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Rye&display=swap');
    
    /* Main background - Dark Earthy Soil Texture with rich soil overlay */
    .stApp {
        background: linear-gradient(rgba(28, 23, 19, 0.88), rgba(28, 23, 19, 0.95)), 
                    url('https://images.unsplash.com/photo-1558441719-74d120a1f9a0?auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #F4EFE6;
    }
    
    /* Sidebar background - Warm Prospector Parchment */
    [data-testid="stSidebar"] {
        background-color: #E2C9A8 !important;
        border-right: 2px solid #5C4938;
    }
    
    /* Force high-contrast dark text on the sidebar so toggles and labels are fully readable */
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div {
        color: #1C1713 !important;
        font-weight: 600;
    }
    
    /* Western Font for Titles & Headers */
    h1, h2, h3 {
        font-family: 'Rye', serif !important;
        color: #E5B84B !important;
    }
    
    /* Monument Valley Desert Canyon Banner Container */
    .banner-container {
        background-image: linear-gradient(rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.55)), 
                          url('https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center;
        border-radius: 12px;
        padding: 45px 25px;
        text-align: center;
        margin-bottom: 25px;
        border: 2px solid #E5B84B;
        box-shadow: 0 8px 20px rgba(0,0,0,0.7);
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
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.6);
    }
    
    /* Dividers - Earthy Copper/Bronze */
    hr {
        border-color: #5C4938;
    }
</style>
""", unsafe_allow_html=True)

# 2. Load API Keys from Secrets & Initialize Gemini Client
try:
    api_key = st.secrets["tmdb_api_key"]
    omdb_api_key = st.secrets["omdb_api_key"]
    gemini_api_key = st.secrets["gemini_api_key"]
    gemini_client = genai.Client(api_key=gemini_api_key)
except Exception:
    st.error("API keys not found in Streamlit Secrets. Please ensure 'tmdb_api_key', 'omdb_api_key', and 'gemini_api_key' are added.")
    st.stop()

# Custom Banner Section with Desert Canyon Theme & Narrative Text
st.markdown("""
<div class="banner-container">
    <h1 style="color: #F4EFE6; margin-bottom: 15px; text-shadow: 3px 3px 6px rgba(0,0,0,0.9); font-family: 'Rye', serif;">The Fossick Finder</h1>
    <p style="color: #FDF6E2; font-size: 1.2rem; font-family: 'Georgia', serif; font-style: italic; max-width: 850px; margin: 0 auto; text-shadow: 2px 2px 4px rgba(0,0,0,0.9);">
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

# Decade / Era Options (Prioritizing 1980s, 1990s, 1970s as requested)
DECADES = {
    "Any Decade / Era": None,
    "1980s": ("1980-01-01", "1989-12-31"),
    "1990s": ("1990-01-01", "1999-12-31"),
    "1970s": ("1970-01-01", "1979-12-31"),
    "2000s": ("2000-01-01", "2009-12-31"),
    "2010s": ("2010-01-01", "2019-12-31"),
    "2020s": ("2020-01-01", "2029-12-31"),
    "1960s and Earlier": ("1900-01-01", "1969-12-31")
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
selected_decade_name = st.sidebar.selectbox("Era / Decade Focus", list(DECADES.keys()))
selected_vibe_name = st.sidebar.selectbox("Select Atmosphere / Tone", list(VIBES.keys()))

st.sidebar.subheader("✨ AI Semantic Layer")
user_mood = st.sidebar.text_area("What are you in the mood for?", placeholder="e.g. A smart sci-fi with a mind-bending plot twist or a feel-good road trip movie")

st.sidebar.subheader("Prospecting Pans")
exclude_animation = st.sidebar.toggle("Filter out Cartoons / Animation", value=False)
black_and_white = st.sidebar.toggle("Classic Black & White Only", value=False)
blurb_keyword = st.sidebar.text_input("Sift plot blurbs for a word", "", placeholder="e.g. gold, space, island")

# Helper: Cascading Retrieval to Prevent Zero-Result Dead Ends
def fetch_cascading_candidates(endpoint, api_key, sort_by, genre_id, decade_range, black_and_white, exclude_animation):
    def build_url(use_genre=True, use_decade=True, use_bw=True):
        u = f"https://api.themoviedb.org/3/discover/{endpoint}?api_key={api_key}&sort_by={sort_by}&vote_count.gte=15"
        if use_genre and genre_id:
            u += f"&with_genres={genre_id}"
        if use_decade and decade_range:
            start_date, end_date = decade_range
            date_field = "primary_release_date" if endpoint == "movie" else "first_air_date"
            u += f"&{date_field}.gte={start_date}&{date_field}.lte={end_date}"
        if use_bw and black_and_white:
            u += "&with_keywords=10183"
        if exclude_animation and genre_id != 16:
            u += "&without_genres=16"
        return u

    # Tier 1: Strict Decade + Genre
    res = requests.get(build_url(use_genre=True, use_decade=True, use_bw=True))
    if res.status_code != 200:
        return None, "error"
    results = res.json().get("results", [])
    fallback_note = None

    # Tier 2: Relax Genre if too few results (keep Decade locked)
    if len(results) < 5 and genre_id:
        res = requests.get(build_url(use_genre=False, use_decade=True, use_bw=True))
        if res.status_code == 200 and res.json().get("results"):
            results = res.json().get("results", [])
            fallback_note = f"Broadened beyond **{selected_genre_name}** within the **{selected_decade_name}** to keep your pan full."

    # Tier 3: Open Quarry (relax Decade & B&W if still under 3 results)
    if len(results) < 3:
        res = requests.get(build_url(use_genre=False, use_decade=False, use_bw=False))
        if res.status_code == 200 and res.json().get("results"):
            results = res.json().get("results", [])
            fallback_note = "Expanded search across all eras to guarantee fresh gems."

    return results, fallback_note


# Initialize Session State for Pagination & Quota Protection
if "unearthed_items" not in st.session_state:
    st.session_state.unearthed_items = []
if "prospector_notes" not in st.session_state:
    st.session_state.prospector_notes = {}
if "display_count" not in st.session_state:
    st.session_state.display_count = 6
if "last_search_params" not in st.session_state:
    st.session_state.last_search_params = None
if "fallback_note" not in st.session_state:
    st.session_state.fallback_note = None

# 4. Discover Button Trigger
current_params = (
    media_type,
    selected_genre_name,
    selected_decade_name,
    selected_vibe_name,
    user_mood.strip(),
    blurb_keyword.strip(),
    exclude_animation,
    black_and_white,
)

if st.sidebar.button("⛏️ Dig for Gems!", type="primary"):
    # If filters haven't changed and we already have items, simply dig 6 deeper!
    if st.session_state.last_search_params == current_params and st.session_state.unearthed_items:
        st.session_state.display_count += 6
    else:
        st.session_state.last_search_params = current_params
        st.session_state.display_count = 6
        st.session_state.prospector_notes = {}
        st.session_state.fallback_note = None

        genre_id = genre_dict[selected_genre_name]
        vibe_data = VIBES[selected_vibe_name]
        decade_range = DECADES[selected_decade_name]
        sort_by = vibe_data["sort"] if vibe_data else "popularity.desc"

        with st.spinner(f"⛏️ Digging through the dirt and gravel for {media_type.lower()}..."):
            items, fallback_note = fetch_cascading_candidates(
                endpoint, api_key, sort_by, genre_id, decade_range, black_and_white, exclude_animation
            )

        if items is not None:
            st.session_state.fallback_note = fallback_note

            # Soft-filter plot blurb keyword
            if blurb_keyword:
                keyword_lower = blurb_keyword.lower()
                filtered_items = [item for item in items if keyword_lower in item.get("overview", "").lower()]
                if filtered_items:
                    items = filtered_items
                else:
                    st.caption(f"No exact plot match for *'{blurb_keyword}'*—passing full vein to the AI Prospector to evaluate.")

            # Combine dropdown Tone/Vibe + free-text Mood
            effective_mood_parts = []
            if selected_vibe_name != "Any Vibe":
                effective_mood_parts.append(f"Tone/Atmosphere: {selected_vibe_name}")
            if user_mood.strip():
                effective_mood_parts.append(f"Specific craving: {user_mood.strip()}")
            combined_mood = " | ".join(effective_mood_parts)

            # Stage 3: Unified Semantic Reranking (Movies + TV Episodes)
            if combined_mood and items:
                with st.spinner("🤖 Gemini AI Prospector is cross-matching blurbs and ranking candidates..."):
                    try:
                        candidate_snippets = []

                        if endpoint == "movie":
                            for i in items[:20]:
                                candidate_snippets.append(
                                    f"- ID: {i.get('id')} | Title: {i.get('title')} ({i.get('release_date', '')[:4]}) | Overview: {i.get('overview')}"
                                )
                        else:
                            expanded_candidates = []
                            for i in items[:5]:
                                show_title = i.get('name')
                                eps = fetch_tvmaze_episode_candidates(show_title)
                                for ep in eps[:12]:
                                    clean_summary = (ep.get('summary') or '').replace('<p>', '').replace('</p>', '')
                                    expanded_candidates.append({
                                        "id": f"{i.get('id')}_ep_{ep.get('id')}",
                                        "title": f"{show_title} - S{ep.get('season')}E{ep.get('number')}: {ep.get('name')}",
                                        "overview": clean_summary,
                                        "parent_show": i
                                    })
                            if expanded_candidates:
                                items = expanded_candidates
                                for i in items[:25]:
                                    candidate_snippets.append(
                                        f"- ID: {i.get('id')} | Episode: {i.get('title')} | Overview: {i.get('overview')}"
                                    )
                            else:
                                for i in items[:20]:
                                    candidate_snippets.append(
                                        f"- ID: {i.get('id')} | Title: {i.get('name')} | Overview: {i.get('overview')}"
                                    )

                        movies_snippet = "\n".join(candidate_snippets)
                        prompt = build_curation_prompt(combined_mood, movies_snippet)
                        ai_res = gemini_client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=prompt,
                            config={"response_mime_type": "application/json"}
                        )
                        parsed_data = json.loads(ai_res.text.strip())

                        if isinstance(parsed_data, dict):
                            for val in parsed_data.values():
                                if isinstance(val, list):
                                    parsed_data = val
                                    break

                        valid_ids = []
                        for entry in parsed_data:
                            item_id = entry.get("id")
                            note_text = entry.get("note")
                            if item_id is not None and note_text:
                                valid_ids.append(str(item_id))
                                st.session_state.prospector_notes[str(item_id)] = note_text

                        # Put AI-curated top picks first, followed by remaining candidates so "Dig Deeper" always has more
                        curated_items = [item for vid in valid_ids for item in items if str(item.get('id')) == vid]
                        remaining_items = [item for item in items if str(item.get('id')) not in valid_ids]
                        if curated_items:
                            items = curated_items + remaining_items
                    except Exception as e:
                        st.warning(f"⚠️ AI Prospector temporarily unavailable ({e}). Showing top TMDB matches instead.")

            st.session_state.unearthed_items = items
        else:
            st.error("💥 Cave-in! Failed to connect to TMDB API. Please check your connection or API key.")

# 5. Display Unearthed Gems from Session State
if st.session_state.fallback_note:
    st.info(f"🧭 **Prospector's Detour:** {st.session_state.fallback_note}")

all_items = st.session_state.unearthed_items
items_to_show = all_items[:st.session_state.display_count]

if items_to_show:
    st.success(f"💎 Strike! Showing {len(items_to_show)} of {len(all_items)} unearthed {media_type.lower()} from the quarry:")

    for item in items_to_show:
        st.markdown('<div class="gem-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])

        poster_path = item.get("poster_path") or item.get("parent_show", {}).get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        title = item.get("title") or item.get("name", "Unknown Title")
        date_val = item.get("release_date") or item.get("first_air_date") or 'N/A'
        if not date_val or date_val == 'N/A':
            date_val = item.get("parent_show", {}).get("first_air_date", "N/A")

        release_year = str(date_val).split("-")[0] if date_val != 'N/A' else ""
        tmdb_rating = item.get('vote_average') or item.get('parent_show', {}).get('vote_average', 5.0)

        # Fetch cross-database ratings from OMDb API
        omdb_rating = "N/A"
        rt_rating = "N/A"
        metacritic = "N/A"

        try:
            clean_title = title.split(" - S")[0] if " - S" in title else title
            omdb_url = f"http://www.omdbapi.com/?apikey={omdb_api_key}&t={requests.utils.quote(clean_title)}"
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

            note = st.session_state.prospector_notes.get(str(item.get('id')))
            if note:
                st.markdown(f"**⛏️ Prospector's Note:** *\"{note}\"*")

            st.write(item.get("overview", "No plot inscription found."))

        st.markdown('</div>', unsafe_allow_html=True)

    # Bottom "Dig Deeper" Button
    if st.session_state.display_count < len(all_items):
        if st.button("⛏️ Dig Deeper (Load 6 More Gems)", use_container_width=True):
            st.session_state.display_count += 6
            st.rerun()
    else:
        st.caption("🪨 You've reached the bedrock of this vein! Adjust your filters on the left to dig a new tunnel.")
elif st.session_state.last_search_params is not None:
    st.warning(f"🪨 Nothing but gravel! No {media_type.lower()} matched those filters.")
else:
    st.info("👈 Grab your **Prospecting Tools** on the left, choose your decade, type what you're craving, and click **⛏️ Dig for Gems!**")

st.sidebar.caption(f"Prompt Engine: `{PROMPT_VERSION}`")
from datetime import date, timedelta
import json
import numpy as np
import requests
import streamlit as st
from google import genai

from prompts.prospector_prompts import PROMPT_VERSION, build_curation_prompt

# ---------------------------------------------------------------------------
# Page Setup & Western Gold Rush Styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="The Fossick Finder",
    page_icon="⛏️",
    layout="wide",
)

st.markdown(
    """
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

    /* Force high-contrast dark text on the sidebar so controls and labels stay readable */
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

    /* Gem Result Card Styling - Excavated Stone & Gem Border */
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
""",
    unsafe_allow_html=True,
)

# Custom Banner Section with Desert Canyon Theme & Narrative Text
st.markdown(
    """
<div class="banner-container">
    <h1 style="color: #F4EFE6; margin-bottom: 15px; text-shadow: 3px 3px 6px rgba(0,0,0,0.9); font-family: 'Rye', serif;">The Fossick Finder</h1>
    <p style="color: #FDF6E2; font-size: 1.2rem; font-family: 'Georgia', serif; font-style: italic; max-width: 850px; margin: 0 auto; text-shadow: 2px 2px 4px rgba(0,0,0,0.9);">
        This app is here because there is so much quality narrative out there. We are so far ahead that just watching whatever is the latest on streaming is the old way of doing things. With the Fossick Finder you can delve into our history by watching the stories that made us. Back then we had more in common than differences --- see for yourself.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------
TV_LOW_TIME_TEXT = (
    "Television episodes back then were meant to be seen one episode at a time. "
    "You can just watch one episode virtually anywhere in the series and not be lost narratively. "
    "Please just lay back and see how we used to live."
)

FREE_AD_SUPPORTED_PROVIDERS = {
    "tubi",
    "plex",
    "pluto tv",
    "the roku channel",
    "freevee",
}

DECADES = {
    "Any Decade / Era": None,
    "1980s": ("1980-01-01", "1989-12-31"),
    "1990s": ("1990-01-01", "1999-12-31"),
    "1970s": ("1970-01-01", "1979-12-31"),
    "2000s": ("2000-01-01", "2009-12-31"),
    "2010s": ("2010-01-01", "2019-12-31"),
    "2020s": ("2020-01-01", "2029-12-31"),
    "1960s and Earlier": ("1900-01-01", "1969-12-31"),
}

VIBES = {
    "Any Vibe": {"sort": "vote_average.desc"},
    "Fun & Uplifting (Feel-Good)": {"keyword": "9799", "sort": "vote_average.desc"},
    "Serious & Thought-Provoking": {"keyword": "1563", "sort": "vote_average.desc"},
    "Dark & Gritty": {"keyword": "10986", "sort": "vote_average.desc"},
    "Light & Quirky / Offbeat": {"keyword": "10287", "sort": "vote_average.desc"},
    "Action-Packed / High Energy": {"keyword": "9715", "sort": "vote_average.desc"},
}

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
    "Western": 37,
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
    "Western": 37,
}


def get_secret(*key_names: str):
    for key in key_names:
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            continue
    return None


tmdb_api_key = get_secret("TMDB_API_KEY", "tmdb_api_key")
omdb_api_key = get_secret("OMDB_API_KEY", "omdb_api_key")
gemini_api_key = get_secret("GEMINI_API_KEY", "gemini_api_key")

if not tmdb_api_key or not gemini_api_key:
    st.error(
        "API keys not found in Streamlit Secrets. Please ensure TMDB and Gemini API keys are configured in `.streamlit/secrets.toml`."
    )
    st.stop()

gemini_client = genai.Client(api_key=gemini_api_key)

# ---------------------------------------------------------------------------
# Ranking, Streaming, Cascading Retrieval & Episode Vector Helpers
# ---------------------------------------------------------------------------
def _parse_year(date_str: str | None) -> int | None:
    if not date_str or len(date_str) < 4:
        return None
    try:
        return int(date_str[:4])
    except ValueError:
        return None


def rank_by_inverse_popularity(items: list[dict]) -> list[dict]:
    """
    Opposite-popularity rubric: lower TMDB popularity and vote counts rank first
    so mainstream evergreens are less likely to crowd out overlooked gems.
    """
    return sorted(
        items,
        key=lambda item: (
            float(item.get("popularity") or 0.0),
            int(item.get("vote_count") or 0),
        ),
    )


def prioritize_recent_non_wide_movies(
    movies: list[dict],
    lookback_years: int = 3,
    wide_vote_threshold: int = 1500,
    wide_popularity_threshold: float = 45.0,
) -> list[dict]:
    """
    Boost movies from recent years that appear to be limited or non-wide releases
    while preserving relative ordering for everything else.
    """
    cutoff_date = date.today() - timedelta(days=365 * lookback_years)
    scored_entries: list[tuple[int, int, dict]] = []

    for idx, movie in enumerate(movies):
        release_str = movie.get("release_date") or ""
        is_within_window = False

        if len(release_str) >= 10:
            try:
                rel_date = date.fromisoformat(release_str[:10])
                if cutoff_date <= rel_date <= date.today():
                    is_within_window = True
            except ValueError:
                pass
        else:
            yr = _parse_year(release_str)
            if yr is not None and date.today().year - lookback_years <= yr <= date.today().year:
                is_within_window = True

        vote_count = movie.get("vote_count") or 0
        popularity = float(movie.get("popularity") or 0.0)
        looks_non_wide = vote_count < wide_vote_threshold and popularity < wide_popularity_threshold

        priority_tier = 0 if (is_within_window and looks_non_wide) else 1
        scored_entries.append((priority_tier, idx, movie))

    scored_entries.sort(key=lambda entry: (entry[0], entry[1]))
    return [entry[2] for entry in scored_entries]


def filter_current_theatrical_keep_rereleases(
    movies: list[dict],
    recent_window_days: int = 90,
) -> list[dict]:
    """
    Exclude movies currently in or freshly entering active theatrical release,
    while preserving older titles and re-releases.
    """
    today = date.today()
    cutoff_recent = today - timedelta(days=recent_window_days)
    current_year = today.year
    filtered: list[dict] = []

    for movie in movies:
        release_str = movie.get("release_date") or ""
        release_year = _parse_year(release_str)
        original_year = _parse_year(movie.get("original_release_date"))
        is_reissue = bool(movie.get("is_rerelease", False))

        if is_reissue or (original_year is not None and original_year < current_year - 1):
            filtered.append(movie)
            continue

        is_recent_theatrical = False
        if len(release_str) >= 10:
            try:
                rel_date = date.fromisoformat(release_str[:10])
                if rel_date >= cutoff_recent:
                    is_recent_theatrical = True
            except ValueError:
                pass
        elif release_year is not None and release_year >= current_year:
            is_recent_theatrical = True

        if not is_recent_theatrical:
            filtered.append(movie)

    return filtered


def get_free_streaming_providers(
    item_id: int | str,
    media_type_api: str,
    api_key: str,
    region: str = "US",
) -> list[str]:
    """Return free ad-supported providers (Tubi, Plex, etc.) for a title, cached in session state."""
    if "watch_provider_cache" not in st.session_state:
        st.session_state.watch_provider_cache = {}

    cache_key = f"{media_type_api}:{item_id}:{region}"
    if cache_key in st.session_state.watch_provider_cache:
        return st.session_state.watch_provider_cache[cache_key]

    url = f"https://api.themoviedb.org/3/{media_type_api}/{item_id}/watch/providers"
    matched: list[str] = []

    try:
        resp = requests.get(url, params={"api_key": api_key}, timeout=6)
        resp.raise_for_status()
        region_info = resp.json().get("results", {}).get(region, {})

        candidate_providers = (region_info.get("free") or []) + (region_info.get("ads") or [])
        for prov in candidate_providers:
            name = (prov.get("provider_name") or "").strip()
            if name.lower() in FREE_AD_SUPPORTED_PROVIDERS and name not in matched:
                matched.append(name)
    except Exception:
        matched = []

    st.session_state.watch_provider_cache[cache_key] = matched
    return matched


def prioritize_free_streaming_items(
    items: list[dict],
    endpoint: str,
    api_key: str,
    max_lookup: int = 20,
    region: str = "US",
) -> list[dict]:
    """Boost items available on free ad-supported streaming apps toward the front."""
    if not items or not api_key:
        return items

    scored: list[tuple[int, int, dict]] = []
    for idx, item in enumerate(items):
        item_copy = dict(item)
        parent_show = item_copy.get("parent_show") if isinstance(item_copy.get("parent_show"), dict) else {}
        lookup_id = item_copy.get("series_tmdb_id") or parent_show.get("id") or item_copy.get("id")
        if idx < max_lookup and lookup_id:
            free_apps = get_free_streaming_providers(
                item_id=lookup_id,
                media_type_api=endpoint,
                api_key=api_key,
                region=region,
            )
            item_copy["free_platforms"] = free_apps
            tier = 0 if free_apps else 1
        else:
            item_copy.setdefault("free_platforms", [])
            tier = 1

        scored.append((tier, idx, item_copy))

    scored.sort(key=lambda entry: (entry[0], entry[1]))
    return [entry[2] for entry in scored]


def _tmdb_discover(
    endpoint: str,
    api_key: str,
    sort_by: str,
    genre_id: int | None = None,
    date_range: tuple[str, str] | None = None,
    black_and_white: bool = False,
    exclude_animation: bool = False,
    min_vote_count: int = 20,
) -> list[dict] | None:
    if not api_key:
        return None

    url = f"https://api.themoviedb.org/3/discover/{endpoint}"
    params = {
        "api_key": api_key,
        "sort_by": sort_by,
        "vote_count.gte": min_vote_count,
        "include_adult": "false",
        "page": 1,
    }

    if genre_id:
        params["with_genres"] = genre_id

    if exclude_animation and genre_id != 16:
        params["without_genres"] = 16

    if black_and_white:
        params["with_keywords"] = "10183"

    if date_range:
        start_date, end_date = date_range
        if endpoint == "movie":
            params["primary_release_date.gte"] = start_date
            params["primary_release_date.lte"] = end_date
        else:
            params["first_air_date.gte"] = start_date
            params["first_air_date.lte"] = end_date

    try:
        resp = requests.get(url, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception:
        return None


def fetch_cascading_candidates(
    endpoint: str,
    api_key: str,
    sort_by: str,
    genre_id: int | None,
    decade_range: tuple[str, str] | None,
    black_and_white: bool,
    exclude_animation: bool,
) -> tuple[list[dict] | None, str | None]:
    # Tier 1: Exact filters
    tier1 = _tmdb_discover(
        endpoint=endpoint,
        api_key=api_key,
        sort_by=sort_by,
        genre_id=genre_id,
        date_range=decade_range,
        black_and_white=black_and_white,
        exclude_animation=exclude_animation,
        min_vote_count=20,
    )
    if tier1 is None:
        return None, None
    if len(tier1) >= 6:
        return tier1, None

    # Tier 2: Relax decade constraint while keeping genre & aesthetic options
    tier2 = _tmdb_discover(
        endpoint=endpoint,
        api_key=api_key,
        sort_by=sort_by,
        genre_id=genre_id,
        date_range=None,
        black_and_white=black_and_white,
        exclude_animation=exclude_animation,
        min_vote_count=15,
    )
    if tier2 and len(tier2) >= 6:
        note = "Exact decade + filter mix returned few matches—widened across all decades for those filters."
        return tier2, note

    # Tier 3: Broaden to genre / vote-average recall without popularity boost
    tier3 = _tmdb_discover(
        endpoint=endpoint,
        api_key=api_key,
        sort_by="vote_average.desc",
        genre_id=genre_id,
        date_range=None,
        black_and_white=False,
        exclude_animation=exclude_animation,
        min_vote_count=25,
    )
    if tier3:
        note = "Tight filter combination ran thin—broadened to top-rated titles in your selected vein."
        return tier3, note

    combined = tier2 or tier1 or []
    return combined, "Showing the closest available matches from the quarry."


def fetch_tvmaze_episode_candidates(show_name: str | None) -> list[dict]:
    if not show_name:
        return []
    try:
        search_url = f"https://api.tvmaze.com/search/shows?q={requests.utils.quote(show_name)}"
        res = requests.get(search_url, timeout=10).json()
        if not res:
            return []
        show_id = res[0].get("show", {}).get("id")
        if not show_id:
            return []
        episodes_url = f"https://api.tvmaze.com/shows/{show_id}/episodes"
        episodes = requests.get(episodes_url, timeout=10).json()
        return episodes if isinstance(episodes, list) else []
    except Exception:
        return []


def _cosine_similarity_matrix(query_vec: list[float], doc_vecs: list[list[float]]) -> np.ndarray:
    q = np.array(query_vec, dtype=np.float32)
    m = np.array(doc_vecs, dtype=np.float32)
    q_norm = np.linalg.norm(q) + 1e-8
    m_norms = np.linalg.norm(m, axis=1, keepdims=True) + 1e-8
    return ((m / m_norms) @ (q / q_norm)).flatten()


def rank_episodes_by_vector(
    client,
    mood_query: str,
    episodes: list[dict],
    top_k: int = 25,
) -> list[dict]:
    if not client or not mood_query.strip() or not episodes:
        return episodes[:top_k]

    if "episode_embeddings" not in st.session_state:
        st.session_state.episode_embeddings = {}

    cache = st.session_state.episode_embeddings
    texts_to_embed = []
    uncached_ids = []

    for ep in episodes:
        ep_id = str(ep.get("id"))
        if ep_id not in cache:
            summary_text = f"{ep.get('title', '')}. {ep.get('overview', '')}".strip()
            uncached_ids.append(ep_id)
            texts_to_embed.append(summary_text or "No synopsis available.")

    if texts_to_embed:
        emb_res = client.models.embed_content(
            model="gemini-embedding-001",
            contents=texts_to_embed,
        )
        for ep_id, emb_obj in zip(uncached_ids, emb_res.embeddings):
            cache[ep_id] = emb_obj.values

    query_res = client.models.embed_content(
        model="gemini-embedding-001",
        contents=mood_query.strip(),
    )
    query_vec = query_res.embeddings[0].values

    valid_episodes = [ep for ep in episodes if str(ep.get("id")) in cache]
    if not valid_episodes:
        return episodes[:top_k]

    doc_vecs = [cache[str(ep.get("id"))] for ep in valid_episodes]
    scores = _cosine_similarity_matrix(query_vec, doc_vecs)
    ranked_indices = np.argsort(scores)[::-1][:top_k]
    return [valid_episodes[int(idx)] for idx in ranked_indices]


# ---------------------------------------------------------------------------
# Sidebar Prospecting Controls
# ---------------------------------------------------------------------------
st.sidebar.header("⛏️ Prospecting Tools")

media_type = st.sidebar.radio("Where are we digging?", ["Movies", "TV Episodes"])
if media_type == "TV Episodes":
    st.sidebar.info(TV_LOW_TIME_TEXT)

endpoint = "movie" if media_type == "Movies" else "tv"
genre_dict = MOVIE_GENRES if endpoint == "movie" else TV_GENRES

selected_genre_name = st.sidebar.selectbox("Choose Your Vein (Genre)", list(genre_dict.keys()))
selected_decade_name = st.sidebar.selectbox("Era / Decade Focus", list(DECADES.keys()))
selected_vibe_name = st.sidebar.selectbox("Select Atmosphere / Tone", list(VIBES.keys()))

st.sidebar.subheader("✨ Speak to the Mountain")
user_mood = st.sidebar.text_area(
    "What mood, plot details, or keywords are you looking for?",
    placeholder="e.g. A smart sci-fi episode with a time loop, or a cozy mystery on an island",
    height=90,
)

st.sidebar.subheader("Prospecting Pans")
exclude_animation = st.sidebar.toggle("Filter out Cartoons / Animation", value=False)
black_and_white = st.sidebar.toggle("Classic Black & White Only", value=False)
prioritize_free_streams = st.sidebar.toggle("Prioritize Free Streaming (Tubi / Plex)", value=True)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Discover Button Trigger
# ---------------------------------------------------------------------------
current_params = (
    media_type,
    selected_genre_name,
    selected_decade_name,
    selected_vibe_name,
    user_mood.strip(),
    exclude_animation,
    black_and_white,
    prioritize_free_streams,
)

if st.sidebar.button("⛏️ Dig for Gems!", type="primary"):
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
        sort_by = vibe_data["sort"] if vibe_data else "vote_average.desc"

        with st.spinner(f"⛏️ Digging through the dirt and gravel for {media_type.lower()}..."):
            items, fallback_note = fetch_cascading_candidates(
                endpoint,
                tmdb_api_key,
                sort_by,
                genre_id,
                decade_range,
                black_and_white,
                exclude_animation,
            )

        if items is not None:
            # Inverse popularity rubric: lower popularity and fewer votes rank ahead of massive hits
            items = rank_by_inverse_popularity(items)
            st.session_state.fallback_note = fallback_note

            if endpoint == "movie":
                filtered_movies = filter_current_theatrical_keep_rereleases(items)
                items = filtered_movies if filtered_movies else items
                items = prioritize_recent_non_wide_movies(items)

            effective_mood_parts = []
            if selected_vibe_name != "Any Vibe":
                effective_mood_parts.append(f"Tone/Atmosphere: {selected_vibe_name}")
            if user_mood.strip():
                effective_mood_parts.append(f"Specific craving: {user_mood.strip()}")
            combined_mood = " | ".join(effective_mood_parts)

            if combined_mood and items and gemini_client:
                with st.spinner("🤖 Gemini AI Prospector is cross-matching blurbs and ranking candidates..."):
                    try:
                        candidate_snippets = []

                        if endpoint == "movie":
                            for i in items[:20]:
                                release_yr = (i.get("release_date") or "")[:4]
                                candidate_snippets.append(
                                    f"- ID: {i.get('id')} | Title: {i.get('title')} ({release_yr}) | Overview: {i.get('overview')}"
                                )
                        else:
                            expanded_candidates = []
                            for i in items[:10]:
                                show_title = i.get("name")
                                eps = fetch_tvmaze_episode_candidates(show_title)
                                for ep in eps[:12]:
                                    raw_summary = ep.get("summary") or ""
                                    clean_summary = (
                                        raw_summary.replace("<p>", "")
                                        .replace("</p>", "")
                                        .replace("<b>", "")
                                        .replace("</b>", "")
                                        .strip()
                                    )
                                    expanded_candidates.append(
                                        {
                                            "id": f"{i.get('id')}_ep_{ep.get('id')}",
                                            "title": f"{show_title} - S{ep.get('season')}E{ep.get('number')}: {ep.get('name')}",
                                            "air_date": ep.get("airdate") or i.get("first_air_date") or "Unknown date",
                                            "overview": clean_summary,
                                            "parent_show": i,
                                        }
                                    )

                            if expanded_candidates:
                                try:
                                    items = rank_episodes_by_vector(
                                        client=gemini_client,
                                        mood_query=combined_mood,
                                        episodes=expanded_candidates,
                                        top_k=25,
                                    )
                                except Exception:
                                    items = expanded_candidates[:25]

                                for i in items[:25]:
                                    air_date = i.get("air_date") or i.get("first_air_date") or "Unknown date"
                                    candidate_snippets.append(
                                        f"- ID: {i.get('id')} | Episode: {i.get('title')} | Air Date: {air_date} | Overview: {i.get('overview')}"
                                    )
                            else:
                                for i in items[:20]:
                                    rel_date = i.get("release_date") or i.get("first_air_date") or "Unknown date"
                                    candidate_snippets.append(
                                        f"- ID: {i.get('id')} | Title: {i.get('title') or i.get('name')} | Release Date: {rel_date} | Overview: {i.get('overview')}"
                                    )

                        movies_snippet = "\n".join(candidate_snippets)
                        prompt = build_curation_prompt(combined_mood, movies_snippet)
                        ai_res = gemini_client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=prompt,
                            config={"response_mime_type": "application/json"},
                        )
                        parsed_data = json.loads((ai_res.text or "").strip())

                        if isinstance(parsed_data, dict):
                            for val in parsed_data.values():
                                if isinstance(val, list):
                                    parsed_data = val
                                    break

                        valid_ids = []
                        if isinstance(parsed_data, list):
                            for entry in parsed_data:
                                if not isinstance(entry, dict):
                                    continue
                                item_id = entry.get("id")
                                note_text = entry.get("note")
                                if item_id is not None and note_text:
                                    sid = str(item_id)
                                    if sid not in valid_ids:
                                        valid_ids.append(sid)
                                    st.session_state.prospector_notes[sid] = note_text

                        curated_items = [
                            item for vid in valid_ids for item in items if str(item.get("id")) == vid
                        ]
                        remaining_items = [
                            item for item in items if str(item.get("id")) not in set(valid_ids)
                        ]
                        if curated_items:
                            items = curated_items + remaining_items
                    except Exception as e:
                        st.warning(f"⚠️ AI Prospector temporarily unavailable ({e}). Showing top matches instead.")

            if prioritize_free_streams and items:
                items = prioritize_free_streaming_items(
                    items=items,
                    endpoint=endpoint,
                    api_key=tmdb_api_key,
                    max_lookup=20,
                )

            st.session_state.unearthed_items = items
        else:
            st.error("💥 Cave-in! Failed to connect to TMDB API. Please check your connection or `.streamlit/secrets.toml`.")

# ---------------------------------------------------------------------------
# Display Unearthed Gems from Session State
# ---------------------------------------------------------------------------
if st.session_state.fallback_note:
    st.info(f"🧭 **Prospector's Detour:** {st.session_state.fallback_note}")

all_items = st.session_state.unearthed_items
items_to_show = all_items[: st.session_state.display_count]

if items_to_show:
    st.success(
        f"💎 Strike! Showing {len(items_to_show)} of {len(all_items)} unearthed {media_type.lower()} from the quarry:"
    )

    for item in items_to_show:
        st.markdown('<div class="gem-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])

        parent_show = item.get("parent_show") if isinstance(item.get("parent_show"), dict) else {}
        poster_path = item.get("poster_path") or parent_show.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        title = item.get("title") or item.get("name", "Unknown Title")
        date_val = item.get("air_date") or item.get("release_date") or item.get("first_air_date") or "N/A"
        if not date_val or date_val == "N/A":
            date_val = parent_show.get("first_air_date", "N/A")

        release_year = str(date_val).split("-")[0] if date_val and date_val != "N/A" else ""
        tmdb_rating = item.get("vote_average")
        if tmdb_rating is None:
            tmdb_rating = parent_show.get("vote_average", 5.0)
        try:
            tmdb_rating = float(tmdb_rating)
        except Exception:
            tmdb_rating = 5.0

        omdb_rating = "N/A"
        rt_rating = "N/A"
        metacritic = "N/A"

        if omdb_api_key:
            try:
                clean_title = title.split(" - S")[0] if " - S" in title else title
                omdb_url = (
                    f"http://www.omdbapi.com/?apikey={omdb_api_key}&t={requests.utils.quote(clean_title)}"
                )
                if release_year:
                    omdb_url += f"&y={release_year}"
                omdb_res = requests.get(omdb_url, timeout=8).json()

                if omdb_res.get("Response") == "True":
                    omdb_rating = omdb_res.get("imdbRating", "N/A")
                    metacritic = omdb_res.get("Metascore", "N/A")
                    for r in omdb_res.get("Ratings", []):
                        if r.get("Source") == "Rotten Tomatoes":
                            rt_rating = r.get("Value", "N/A")
            except Exception:
                pass

        cheesiness_score = max(1, min(10, int((10 - tmdb_rating) * 1.2 + 2)))
        if cheesiness_score >= 8:
            cheese_badge = "🧀 Fool's Gold / Super Cheesy Cult Classic"
        elif cheesiness_score >= 5:
            cheese_badge = "🍿 Rough Cut / Mildly Cheesy Fun"
        else:
            cheese_badge = "💎 Flawless Cut / Prestigious"

        free_platforms = item.get("free_platforms") or []

        with col1:
            if poster_url:
                st.image(poster_url, width=150)
            else:
                st.write("🪨 No poster unearthed")

        with col2:
            st.subheader(f"💎 {title}")
            st.write(f"**Unearthed (Release / Air Date):** {date_val}")
            if free_platforms:
                st.write(f"**Free Ad-Supported Streaming:** {', '.join(free_platforms)}")
            st.write(
                f"**Appraisal:** TMDB: `{tmdb_rating:.1f}/10` | IMDb: `{omdb_rating}` | "
                f"Rotten Tomatoes: `{rt_rating}` | Metacritic: `{metacritic}`"
            )
            st.write(f"**Purity & Cheese:** `{cheesiness_score}/10` — {cheese_badge}")

            note = st.session_state.prospector_notes.get(str(item.get("id")))
            if note:
                st.markdown(f"**⛏️ Prospector's Historical Note:** *\"{note}\"*")

            st.write(item.get("overview") or "No plot inscription found.")

        st.markdown("</div>", unsafe_allow_html=True)

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
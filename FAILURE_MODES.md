# 🛡️ Failure Modes & Mitigations Log

This document tracks real retrieval, prompt, and state-management failure modes identified during development and evaluation of **The Fossick Finder**, along with the architectural mitigations implemented to resolve them.

---

## 1. Zero-Result Over-Filtering ("Filter Collapse")

* **Failure Mode:** Combining strict TMDB metadata filters (e.g., `1970s` + `Sci-Fi` + `Black & White` + `Keyword`) frequently returned `0` candidates from `/discover`, resulting in empty screens even when adjacent titles existed.
* **Root Cause:** Boolean `AND` filtering on sparse metadata fields creates brittle intersection boundaries.
* **Mitigation:** Implemented **3-Tier Cascading Retrieval** (`fetch_cascading_candidates`):
  * **Tier 1:** Queries TMDB with all user-selected constraints.
  * **Tier 2:** If fewer than 6 candidates return, automatically drops the decade boundary while preserving genre and aesthetic filters.
  * **Tier 3:** Falls back to broad genre/popularity recall if Tier 2 remains sparse.
  * Displays an explicit `st.info` *"Prospector's Detour"* banner whenever fallback relaxation triggers so search behavior remains transparent.

---

## 2. Show-Level vs. Episode-Level Mismatch in TV Discovery

* **Failure Mode:** When users searched TV shows for specific narrative tropes (e.g., *"A bottle episode trapped in one room"* or *"A musical episode"*), TMDB's series-level `overview` lacked episode-specific plot details, causing Gemini to miss obvious matches.
* **Root Cause:** Series overviews summarize multi-season premises rather than individual episode arcs.
* **Mitigation:** Built a **Cross-API Episode Expansion Stage** using the **TVmaze API** (`fetch_tvmaze_episode_candidates`):
  * Takes the top 5 TMDB series candidates, queries TVmaze for episode-level summaries, strips HTML markup, and constructs composite candidate IDs (`{tmdb_id}_ep_{tvmaze_ep_id}`).
  * Feeds up to 25 granular episode synopses into Gemini's reranking prompt while preserving parent show poster art and ratings for display.

---

## 3. LLM Candidate Hallucination & ID Drift

* **Failure Mode:** Early prompt iterations occasionally hallucinated movie titles not present in the TMDB candidate pool or returned malformed JSON wrapped in Markdown fences (` ```json `).
* **Root Cause:** Unconstrained text generation without strict schema enforcement or grounded ID verification.
* **Mitigation:**
  * Enforced `response_mime_type="application/json"` via the Google GenAI SDK.
  * Instructed Gemini in `prompts/prospector_prompts.py` to return exact candidate IDs (`id`), integer scores (`1–10`), and single-sentence editorial justifications (`note`).
  * Added deterministic post-processing in `app.py` that filters AI outputs strictly against the in-memory candidate ID map—dropping any ungrounded IDs silently.

---

## 4. Redundant API Calls & Free-Tier Quota Exhaustion on Pagination

* **Failure Mode:** Re-running the full TMDB + TVmaze + Gemini pipeline every time a user clicked *"Dig for Gems!"* or wanted to view more than the top 6 results exhausted daily free-tier Gemini rate limits (`429 RESOURCE_EXHAUSTED`) and introduced unnecessary latency.
* **Root Cause:** Stateless Streamlit reruns re-executed API calls on every button interaction.
* **Mitigation:**
  * Implemented **`st.session_state` Candidate Caching & Pagination** (`unearthed_items`, `display_count`, `last_search_params`).
  * Clicking **"⛏️ Dig Deeper (Load 6 More Gems)"** slices the next 6 items directly from the cached ranked pool (`curated_items + remaining_items`) with **zero additional API calls**.
  * Wrapped Gemini generation in a `try/except` block that gracefully degrades to TMDB's native ranking with a non-blocking `st.warning` banner if API quotas are reached.

---

## 5. Missing Cross-Database Ratings for Episode Results

* **Failure Mode:** Querying OMDb with a composite episode title (e.g., `"The Twilight Zone - S1E22: The Monsters Are Due on Maple Street"`) caused OMDb lookups to return `Response: False`, displaying `N/A` for IMDb, Rotten Tomatoes, and Metacritic scores.
* **Root Cause:** OMDb title search expects the root series name rather than concatenated season/episode strings.
* **Mitigation:** Normalized title extraction prior to OMDb lookup (`title.split(" - S")[0]`) so episode cards inherit accurate parent-series ratings across all three review aggregators.

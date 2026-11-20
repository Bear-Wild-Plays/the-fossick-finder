The Fossick Finder — Progress & Milestone Log

This document tracks completed features, model alignments, known runtime edge cases, and next testing steps for The Fossick Finder.

1. Completed Features & Architecture

Western Gold Rush UI & Narrative Banner: Custom Streamlit styling with dark soil textures, parchment prospecting sidebar, gold-nugget action buttons, Monument Valley desert canyon banner with historical narrative text, and TV episode low-time guidance.

Inverse-Popularity Ranking (rank_by_inverse_popularity): Sorts candidate titles by lower TMDB popularity and vote counts first so mainstream evergreens do not crowd out overlooked or archival gems.

Cascading Candidate Retrieval (fetch_cascading_candidates): Progressively broadens TMDB discovery filters across tiers when exact era/genre/aesthetic combinations return thin results.

Movie Release & Re-Release Filtering: Excludes recent theatrical releases while preserving older titles and re-releases, and boosts recent non-wide releases (prioritize_recent_non_wide_movies).

TV Episode Expansion & Semantic Vector Ranking: Expands candidate shows via TVmaze episode listings and ranks episode synopses against mood/query embeddings (gemini-embedding-001) using cosine similarity with session-state caching.

Free Ad-Supported Streaming Prioritization: Checks TMDB watch providers for free ad-supported services (such as Tubi, Plex, Pluto TV, The Roku Channel, and Freevee) and surfaces available options when enabled.

Session-State Pagination ("Dig Deeper"): Caches unearthed results and Prospector's Historical Notes in st.session_state so users can load additional gems without re-running curation unnecessarily.

Multi-Source Ratings & Cheese Meter: Displays TMDB ratings alongside IMDb, Rotten Tomatoes, and Metacritic scores (via OMDb when configured) plus a playfulness/cheese indicator.

2. Model & Repository Alignment

Curation & Evaluation Model (gemini-3.8-flash): Standardized across app.py (curation and Prospector's Historical Notes), evals/run_eval.py (generation and evaluation judge), and README.md (badges and architecture notes).

Embeddings Model (gemini-embedding-001): Retained for episode synopsis and mood vector ranking in app.py.

3. Known Issues & Operational Notes

Transient 503 UNAVAILABLE Model Spikes: High-demand spikes on gemini-3.8-flash can trigger temporary 503 errors during generate_content. When this happens, the app's fallback handler catches the error and displays top vector/TMDB/inverse-popularity matches rather than crashing.

Local vs. Deployed Git Sync: Saving app.py locally updates http://localhost:8501 after a rerun, while live hosted deployments only update after git add, git commit, and git push complete and redeploy.

Secrets & Key Boundaries: Keep .streamlit/secrets.toml and API keys out of Git commits and external chats; note that external assistants (such as Claude) can help review code or write tests, but do not supply Google Gemini server capacity or swap directly into the Gemini client without SDK changes.

4. Next Testing & Rollout Steps

Verify Local Rerun & UI Elements: Confirm app.py is saved on disk, refresh http://localhost:8501 (R or Ctrl + Shift + R), and verify the Monument Valley banner, parchment sidebar, TV episode note, and Prompt Engine caption appear.

Run End-to-End Search Checks:

TV Episodes: Test a decade + mood/keyword query (such as 1970s/1980s with a specific motif) to verify episode expansion, vector ranking, inverse-popularity sorting, and Prospector's Notes when gemini-3.8-flash responds cleanly.

Movies: Test a decade, genre, and mood with free-streaming prioritization toggled on and off.

Test "Dig Deeper" Pagination: Click Dig Deeper (Load 6 More Gems) on a result set and confirm display_count advances smoothly.

Resilience Improvement (Optional Next Enhancement): Add retry/backoff and/or a fallback model around generate_content in app.py to reduce missed Prospector's Notes during 503 demand spikes.

Commit & Push to GitHub: Stage, commit, and push app.py, PROGRESS.md, and any updated docs to GitHub, then confirm the live hosted app reflects the changes.

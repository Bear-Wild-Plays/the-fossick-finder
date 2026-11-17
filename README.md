### HeLLLoooooo therrrrrrrrre.... — I am Bear Wild 👋, (real name, Sean Wilda)
**Content Engineer | AI Product Quality, Prompt Architecture & Evaluation Systems**

I bridge **editorial judgment, user experience, and LLM reliability**—turning subjective human taste into structured rubrics, golden datasets, and measurable AI product improvements. As a Brooklyn area playwright I have swirled the cauldron of creativity and applied creativity in near zero budget scenarios as well as full-fledged productions to excellent reviews. At my corporate job, after training an AI that AI absorbed my position, so I decided to level-up and train myself on the technical side of things. Doing so I saw a perfect place for me. I have never been one thing my whole life, I mainly existed in-between places. My niche is so niched that only AI, ha, could create a position for me --- a Content Engineer. I know the responsibilities are perfectly suited for me, but that is not enough. So, with this GitHub page, The Fossick Finder, and my website I have faith I can prove I fit in the exact shape niched out for a Content Engineer position. 

---

### 🔍 Featured Work: Content Engineering & LLM Evaluation

# ⛏️ The Fossick Finder

**An AI-powered film & TV discovery engine combining multi-stage cascading retrieval, episode-level TVmaze metadata enrichment, and structured LLM semantic reranking.**

[![Live App](https://img.shields.io/badge/Streamlit-Live_Demo-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://thefossickfinder.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini API](https://img.shields.io/badge/Google_Gemini-3.8_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

---

## 🎯 Project Overview

Traditional streaming search engines rely on rigid tag matching and popularity sorting—forcing users to scroll endlessly when searching for specific narrative vibes (e.g., *"A tense time-loop bottle episode"* or *"Moody 1970s neo-noir with a cynical detective"*).

**The Fossick Finder** solves this by treating media discovery as a **two-stage retrieval and editorial curation pipeline**:
1. **3-Tier Cascading Retrieval (Recall):** Queries TMDB with structured metadata filters (Decade, Genre, Vibe/Sort) and automatically relaxes constraints when candidate pools run dry—guaranteeing zero dead-end searches.
2. **Unified Semantic Reranking & Episode Expansion (Precision):** Enriches TV candidates with granular episode synopses via the **TVmaze API**, then uses **Google Gemini (`gemini-3.8-flash`)** with strict JSON schema enforcement to rank the top 6 matches and generate bespoke *Prospector's Notes*.

---

## 🏗️ System Architecture

```text
User Query (Decade + Genre + Vibe + Free-Text Mood)
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ Stage 1: 3-Tier Cascading Candidate Recall (TMDB API)    │
│  • Tier 1: Exact Decade + Genre + Aesthetic Filters      │
│  • Tier 2: Relax Decade constraint (if < 6 candidates)   │
│  • Tier 3: Broaden to top-rated genre/vibe pool          │
└──────────────────────────────────────────────────────────┘
       │
       ├─── [Movies] ──────────────────────────┐
       │                                       ▼
       └─── [TV Shows] ──► Stage 2: TVmaze Episode Expansion
                            • Fetches granular episode synopses
                            • Strips HTML & builds composite IDs
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────┐
│ Stage 3: Semantic Reranking & Editorial Curation         │
│  • Decoupled prompt engine (prompts/prospector_prompts)  │
│  • Structured JSON output (Top 6 ranked matches + Notes) │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ Stage 4: Cross-Database Appraisal & Session Pagination   │
│  • Enriches with IMDb, Rotten Tomatoes & Metacritic      │
│  • st.session_state "Dig Deeper" loads 6 more gems       │
│    without burning redundant LLM or API quota            │
└──────────────────────────────────────────────────────────┘

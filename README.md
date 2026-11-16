# ⛏️ The Fossick Finder — Semantic Media Discovery & Curation Engine

> **Live App:** [Launch The Fossick Finder on Streamlit Cloud](https://thefossickfinder.streamlit.app)  
> **Domain Focus:** Content Engineering, Prompt Architecture, Editorial Rubrics & Automated LLM Evaluation

---

## 1. Executive Summary
Traditional streaming interfaces optimize for engagement on recent releases, burying decades of cinema and television history behind rigid genre tags. **The Fossick Finder** reframes media discovery as a curated, natural-language "prospecting" experience—with dedicated era mining across the **1980s, 1990s, and 1970s**. 

Users combine deterministic metadata filters (decade, genre, animation/B&W pans) with an **LLM Semantic Curation Layer (`gemini-2.5-flash`)** that evaluates plot subtext, ranks matches against a structured editorial rubric, and generates concise, persona-driven **Prospector's Notes**.

---

## 2. System & Prompt Architecture

```text
[User Mood Query + Era/Vibe Filters]
                 │
                 ▼
┌─────────────────────────────────┐
│  1. Deterministic Mining        │ ──► TMDB Discover API (1980s/90s/70s Era, Genre, Keywords)
└─────────────────────────────────┘
                 │
                 ▼ (Candidate Pool: Top 15 Titles + Plot Overviews)
┌─────────────────────────────────┐
│  2. Semantic Re-Ranking         │ ──► Gemini 2.5 Flash + Versioned Rubric (`prompts/`)
│     & Editorial Notes           │     (Scores emotional subtext, enforces zero hallucination)
└─────────────────────────────────┘
                 │
                 ▼ (Curated JSON: Ranked IDs + ≤35-Word Prospector's Notes)
┌─────────────────────────────────┐
│  3. Multi-Source Appraisal      │ ──► OMDb API (IMDb, Rotten Tomatoes, Metacritic)
│     & Purity Scoring            │     + Custom "Purity & Cheese" Heuristic
└─────────────────────────────────┘

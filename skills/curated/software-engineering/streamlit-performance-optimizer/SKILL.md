---
name: streamlit-performance-optimizer
description: Analyze and optimize Streamlit app frontend performance using caching, fragments, state, and backend offloading.
---

# Streamlit Performance Optimizer

This skill turns Claude into a performance engineer for Streamlit apps, focusing on frontend responsiveness and user-perceived speed for dashboards and agentic UIs.

The skill assumes:
- The app is written in Python using Streamlit.
- The user can share code snippets, architecture notes, and rough traffic/data volume.
- Changes can be made to both app code and upstream services (APIs, databases, batch jobs).

## When to Use This Skill

- Streamlit UI feels sluggish when users interact with widgets.
- The app re-runs heavy computations on every interaction.
- Large dataframes, images, or charts cause long render times.
- You need the app to handle more concurrent users without timeouts.
- You are integrating LLM/agent backends and want snappy frontends.

## What This Skill Does

When this skill is active, Claude should:

1. **Profile the architecture (conceptually)**
   - Ask for or infer: data flow, key pages, heavy computations, API/database calls.
   - Identify which parts run on each rerun and which should be cached or offloaded.

2. **Optimize Streamlit’s execution model**
   - Minimize unnecessary reruns caused by widget layout and state usage.
   - Propose a decomposition into logical sections (e.g., sidebar filters, main charts, expensive summaries).
   - Where available, recommend fragment-based patterns or partial rerender strategies supported by the user’s Streamlit version.

3. **Design a caching and state strategy**
   - Decide where to apply `st.cache_data` vs `st.cache_resource`.
   - Propose `st.session_state` usage to persist inputs, intermediate results, and long-lived resources.
   - Ensure cache keys are stable and invalidation rules are clear.
   - Avoid caching data that changes on every request unless explicitly required.

4. **Offload heavy work from the frontend**
   - Suggest moving expensive tasks into:
     - Background workers, tasks, or batch jobs.
     - API endpoints or microservices the Streamlit app can call.
     - Database-side aggregations or materialized views.
   - Propose request/response contracts that keep payloads small and predictable.

5. **Improve data and rendering patterns**
   - Recommend pagination, virtualized tables, or sampling for large datasets.
   - Suggest pre-aggregation instead of aggregating on every interaction.
   - Reduce image/chart payload sizes and complexity when possible.
   - Use placeholder containers and progressive loading for large components.

6. **Refactor code for maintainability**
   - Break monolithic `streamlit_app.py` into modules (data, services, ui components, layout).
   - Separate pure computation from UI code to make performance tuning easier.
   - Introduce clear interfaces for agents/LLM calls to enable caching and retries.

## Instructions

When using this skill, follow these steps:

1. **Gather context**
   - Ask the user for:
     - The current Streamlit version.
     - A description of the slow interactions (which widgets/pages, typical latency).
     - Any constraints (no new infra, must stay single-file, etc.).
   - Request representative code snippets:
     - App entry point and layout.
     - Data loading and preprocessing logic.
     - Any long-running functions or LLM/agent calls.

2. **Identify bottlenecks**
   - Trace, in natural language, what executes on each rerun from top to bottom.
   - Mark steps as:
     - “One-time per session”
     - “Rarely changes”
     - “Changes on most interactions”
   - Highlight:
     - Repeated API/database calls.
     - Recomputed expensive transforms (groupbys, joins, model inference).
     - Large objects being rebuilt (big dataframes, charts, images).

3. **Propose a performance plan**
   - Present a short bullet list of the top 3–5 changes with highest impact.
   - For each change, specify:
     - What to modify.
     - Expected impact (qualitative).
     - Any trade-offs (memory vs speed, freshness vs caching).

4. **Write concrete code changes**
   - Provide ready-to-paste code blocks that:
     - Wrap appropriate functions with `@st.cache_data` or `@st.cache_resource`.
     - Introduce or refactor `st.session_state` usage.
     - Move heavy logic into helper functions or modules.
     - Implement pagination or lazy loading for large views.
   - Keep examples idiomatic for the user’s Streamlit version.

5. **Optimize for LLM/agent-based apps (when applicable)**
   - Batch or debounce calls to LLM backends instead of calling on every keystroke.
   - Cache LLM outputs where semantics allow (e.g., prompt + parameters as key).
   - Separate UI responsiveness from background agent work using:
     - Status indicators and async patterns where available.
     - Polling or streaming APIs where appropriate.

6. **Validate and iterate**
   - After proposing changes, ask the user to test and report:
     - New response times for key interactions.
     - Any cache-related bugs or stale data issues.
   - Refine caching and layout based on feedback.
   - Suggest lightweight logging or timing utilities to measure improvements.

7. **Document the performance profile**
   - Offer a brief “Performance Notes” section the user can add to their README:
     - Key optimizations applied.
     - How to run under load.
     - Known limitations or bottlenecks.

## Examples

### Example 1: Slow filters on large dataset

User reports:
- 5–8 second delays when adjusting filters on a 5M-row dataset.
- Data loaded from a database on each interaction.

Actions:
- Add `@st.cache_data` around the database read with a clear TTL.
- Move heavy aggregations into the database query.
- Implement pagination in the UI for tables.
- Use a lighter sample for quick exploratory charts, with a button for “full detail”.

### Example 2: LLM-backed Streamlit chat feels laggy

User reports:
- Every message triggers slow agent logic and recomputation of history.
- Long histories make things worse over time.

Actions:
- Store conversation history in `st.session_state` and only append new messages.
- Cache model/tool initialization with `@st.cache_resource`.
- Introduce a background task pattern or async calls where supported.
- Add a “lightweight mode” that limits tokens or tools for quick interactions.

### Example 3: Monolithic app difficult to tune

User provides a single large `app.py`.

Actions:
- Propose a modular structure:
  - `data_layer.py` for loading/cacheable functions.
  - `services.py` for API/LLM/agent calls.
  - `components.py` for reusable UI blocks.
  - `app.py` for layout and routing.
- Show code snippets for each module and import pattern.
- Highlight where to place caching decorators and session state management.

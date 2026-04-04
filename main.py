import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlparse
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google_play_scraper import reviews, Sort, search, app as get_app_details
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)


def create_model():
    return genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config=genai.GenerationConfig(
            thinking_config={"thinking_budget": 0}
        ),
    )


@st.cache_data(show_spinner=False)
def search_apps(query, lang="en", country="us", limit=10):
    """
    Search Google Play apps by name and return lightweight result metadata.
    """
    if not query or not query.strip():
        return []

    try:
        results = search(
            query,
            lang=lang,
            country=country.upper(),
            n_hits=limit,
        )

        apps = []
        for result in results:
            app_id = result.get("appId")
            if not app_id:
                continue

            apps.append({
                "title": result.get("title", app_id),
                "developer": result.get("developer", "Unknown developer"),
                "app_id": app_id,
            })

        return apps

    except Exception as e:
        print(f"❌ Error searching apps: {e}")
        return []


def extract_app_id_from_url(value):
    """
    Extract Google Play package id from a Play Store URL.
    """
    if not value or "play.google.com" not in value:
        return None

    try:
        parsed = urlparse(value.strip())
        query_params = parse_qs(parsed.query)
        app_ids = query_params.get("id", [])
        return app_ids[0].strip() if app_ids and app_ids[0].strip() else None
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def resolve_app_from_url(app_id, lang="en", country="us"):
    """
    Resolve app metadata from a Google Play package id.
    """
    if not app_id:
        return None

    try:
        result = get_app_details(app_id, lang=lang, country=country.upper())
        return {
            "title": result.get("title", app_id),
            "developer": result.get("developer", "Unknown developer"),
            "app_id": app_id,
        }
    except Exception as e:
        print(f"❌ Error resolving app from URL: {e}")
        return {
            "title": app_id,
            "developer": "Unknown developer",
            "app_id": app_id,
        }


def parse_json_response(response_text):
    """
    Strip Markdown code fences and parse a JSON response body.
    """
    cleaned = response_text.strip()

    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        if len(parts) >= 2:
            cleaned = parts[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

    return json.loads(cleaned)


@st.cache_data(show_spinner=False, ttl=900)
def get_reviews(app_name, count=50, rating_filter=0, sort_order=1, selected_ratings=None, lang="en", country="us"):
    """
    Fetch reviews from Google Play and filter by rating and sort order.
    Returns a list of review dicts with 'text' and 'rating'.
    """
    normalized_ratings = tuple(sorted(selected_ratings)) if selected_ratings else ()
    ratings_to_filter = normalized_ratings if normalized_ratings else (() if rating_filter == 0 else (rating_filter,))
    batch_size = min(max(count, 50), 200)

    print(f"\n📱 Fetching reviews from {app_name}...")
    if ratings_to_filter:
        print(f"   Target: {count} reviews with ratings {ratings_to_filter}")
    
    try:
        # Map sort order to Sort enum
        sort_map = {
            1: Sort.NEWEST,
            2: Sort.MOST_RELEVANT,
            3: Sort.NEWEST,  # Using NEWEST as fallback for highest rated
            4: Sort.NEWEST   # Using NEWEST as fallback for lowest rated
        }
        sort_by = sort_map.get(sort_order, Sort.NEWEST)

        filtered_reviews = []
        continuation_token = None
        seen_reviews = set()
        max_pages = 5 if ratings_to_filter else 2

        for _ in range(max_pages):
            reviews_data, continuation_token = reviews(
                app_name,
                count=batch_size,
                sort=sort_by,
                continuation_token=continuation_token,
                lang=lang,
                country=country.upper(),
            )

            if not reviews_data:
                break

            for review in reviews_data:
                review_id = review.get("reviewId") or review.get("at")
                if review_id in seen_reviews:
                    continue

                seen_reviews.add(review_id)
                rating = review.get("score", 0)
                if ratings_to_filter and rating not in ratings_to_filter:
                    continue

                review_date = review.get("at")
                filtered_reviews.append({
                    "text": review.get("content", ""),
                    "rating": rating,
                    "date": review_date.isoformat() if review_date else "N/A",
                })

                if len(filtered_reviews) >= count:
                    break

            if len(filtered_reviews) >= count or not continuation_token:
                break
        
        # Determine sort name
        sort_names = {
            1: "Most recent",
            2: "Most helpful",
            3: "Highest rated",
            4: "Lowest rated"
        }
        
        rating_text = f"ratings {ratings_to_filter}" if ratings_to_filter else "all ratings"
        
        print(f"\n✅ Found {len(filtered_reviews)} reviews")
        print(f"   Rating: {rating_text}")
        print(f"   Sort: {sort_names.get(sort_order, 'Most recent')}")
        
        return filtered_reviews
    
    except Exception as e:
        print(f"❌ Error fetching reviews: {e}")
        return []


@st.cache_data(show_spinner=False, ttl=3600)
def analyze_review(review_text, app_name):
    """
    Analyze and validate a single review using one Gemini request.
    Returns insight as JSON.
    """
    prompt = f"""
You are a senior Product Manager with 20 years of experience conducting user research.

Your job is to read a user review, extract a structured product insight, and validate whether the opportunity is feasible for this app.

App: "{app_name}"
Review: "{review_text}"

Respond ONLY in valid JSON with this exact structure:

{{
    "theme": "Choose the most fitting category from this list: App Performance, App Crashes, Battery Drain, Loading Speed, Offline Mode, Data Accuracy, GPS Accuracy, Search Quality, Recommendation Quality, Onboarding Flow, Navigation Complexity, UI Clarity, Feature Discovery, Login Issues, Account Sync, Paywall Friction, Pricing Fairness, Free Tier Value, Subscription Management, Notification Overload, Alert Relevance, Social Features, Community Trust, Privacy Controls, Data Trust, Privacy Settings, Third-party Sync, Device Compatibility, Customer Support, Update Quality. If none fits, create a 2-3 word category.",

  "problem_statement": "One clear sentence. What is broken from the user's perspective. Start with 'Users cannot...' or 'Users struggle to...'",

  "insight": "One sentence. The deeper reason behind the complaint - what this tells us about user behavior or expectations.",

  "opportunity": "One sentence. A specific, buildable product solution. Start with an action verb (Add, Show, Allow, Fix, Enable, Improve).",

  "acceptance_criteria": "One sentence. How we would know this opportunity is successfully delivered. Start with 'Success when...'",

  "priority_signal": "high, medium, or low - based on how much this impacts the core value proposition of the app",

    "confidence": "high, medium, or low - based on how clearly the review supports this insight",

    "validation": {{
        "verdict": "feasible / out_of_scope / already_exists",
        "reason": "one sentence explanation"
    }}
}}

Rules:
- Maximum 20 words per field
- No technical jargon
- Write as if briefing a developer and a designer simultaneously
- Be consistent with theme naming across reviews
- Validate the opportunity against this app's likely scope before answering
- JSON only, no extra text
"""
    
    try:
        response = create_model().generate_content(prompt)
        insight = parse_json_response(response.text)

        # Normalize field names so downstream code can use consistent keys.
        # Gemini returns: problem_statement, insight, opportunity
        # Existing pipeline expects: root_problem, user_gap, product_opportunity
        if "root_problem" not in insight and "problem_statement" in insight:
            insight["root_problem"] = insight.get("problem_statement")
        if "user_gap" not in insight and "insight" in insight:
            insight["user_gap"] = insight.get("insight")
        if "product_opportunity" not in insight and "opportunity" in insight:
            insight["product_opportunity"] = insight.get("opportunity")

        if "validation" not in insight or not isinstance(insight.get("validation"), dict):
            insight["validation"] = {
                "verdict": "unknown",
                "reason": "Validation not returned by model",
            }

        return insight
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error analyzing review: {e}")
        return None


def analyze_review_with_validation(review_text, app_name):
    """
    Run the full AI pipeline for a single review.
    """
    return analyze_review(review_text, app_name)


def analyze_reviews_concurrently(reviews_list, app_name, max_reviews=10, max_workers=4, progress_callback=None):
    """
    Analyze reviews concurrently to reduce total wait time.
    Returns successful review/insight pairs preserving input order.
    """
    target_reviews = reviews_list[:max_reviews]
    if not target_reviews:
        return []

    worker_count = min(max_workers, len(target_reviews))
    results_by_index = {}
    completed_reviews = 0

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(analyze_review_with_validation, review["text"], app_name): index
            for index, review in enumerate(target_reviews)
        }

        for future in as_completed(future_map):
            index = future_map[future]
            try:
                insight = future.result()
            except Exception as e:
                print(f"❌ Error processing review {index + 1}: {e}")
                insight = None

            if insight:
                results_by_index[index] = {
                    "review": target_reviews[index],
                    "insight": insight,
                }

            completed_reviews += 1
            if progress_callback:
                progress_callback(completed_reviews, len(target_reviews))

    return [results_by_index[index] for index in sorted(results_by_index)]


def analyze_multiple_reviews(reviews_list, app_name, max_reviews=10):
    """
    Analyze multiple reviews and aggregate insights with validation.
    Returns list of insights with validation verdicts.
    """
    print(f"\n🤖 Analyzing {min(len(reviews_list), max_reviews)} reviews...")
    
    review_payload = [{"text": review} for review in reviews_list[:max_reviews]]
    analyzed_pairs = analyze_reviews_concurrently(review_payload, app_name, max_reviews=max_reviews)
    insights = [pair["insight"] for pair in analyzed_pairs]
    
    print(f"✅ Analyzed {len(insights)} reviews\n")
    
    return insights


def save_insights_to_file(insights, app_name):
    """
    Save insights to JSON file.
    """
    filename = f"{app_name}_insights.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Insights saved to: {filename}")
    return filename


def insights_to_dataframe(insights, reviews_data):
    """
    Convert insights list to a structured DataFrame.
    """
    data = []
    
    for i, insight in enumerate(insights, 1):
        review = reviews_data[i-1]  # Corresponding review data
        row = {
            "review_id": i,
            "review_date": review.get('date', "N/A"),
            "rating": review['rating'],
            "original_comment": review['text'],
            "root_problem": insight.get("root_problem", "N/A"),
            "user_gap": insight.get("user_gap", "N/A"),
            "product_opportunity": insight.get("product_opportunity", "N/A"),
            "theme": insight.get("theme", "N/A"),
            "confidence": insight.get("confidence", "N/A"),
            "verdict": insight.get("validation", {}).get("verdict", "N/A"),
            "validation_reason": insight.get("validation", {}).get("reason", "N/A")
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    return df


def save_dataframe_to_csv(df, app_name):
    """
    Save DataFrame to CSV file.
    """
    filename = f"{app_name}_insights.csv"
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"✅ DataFrame saved to: {filename}")
    return filename


def group_opportunities_by_theme(insights):
    """
    Group similar product opportunities by theme using AI.
    """
    opportunities = [insight.get("product_opportunity", "") for insight in insights]
    
    prompt = f"""Analyze these product opportunities and group them by theme/category:

{chr(10).join([f"{i+1}. {opp}" for i, opp in enumerate(opportunities)])}

Respond with JSON grouping them by 2-4 main themes:
{{
  "themes": [
    {{
      "theme_name": "Theme name",
      "opportunities": [1, 3, 5],
      "summary": "What these opportunities have in common"
    }}
  ]
}}

Only respond with valid JSON."""
    
    try:
        response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        grouped = json.loads(response_text)
        return grouped.get("themes", [])
    
    except Exception as e:
        print(f"❌ Error grouping opportunities: {e}")
        return []


def display_grouped_opportunities(insights, themes):
    """
    Display opportunities grouped by theme.
    """
    print("\n" + "="*60)
    print("📊 OPPORTUNITIES GROUPED BY THEME")
    print("="*60)
    
    for theme in themes:
        theme_name = theme.get("theme_name", "Unknown")
        summary = theme.get("summary", "")
        opportunity_indices = theme.get("opportunities", [])
        
        print(f"\n🏷️  {theme_name.upper()}")
        print(f"   {summary}")
        print(f"   Opportunities: {opportunity_indices}")
        
        for idx in opportunity_indices:
            if 0 < idx <= len(insights):
                opp = insights[idx - 1].get("product_opportunity", "")
                print(f"   • {opp[:100]}...")


def create_prioritized_backlog(insights, themes):
    """
    Create a prioritized backlog ranked by frequency and feasibility.
    """
    backlog = []
    
    for theme in themes:
        theme_name = theme.get("theme_name", "Unknown")
        summary = theme.get("summary", "")
        opportunity_indices = theme.get("opportunities", [])
        
        # Count feasible opportunities in this theme
        feasible_count = 0
        for idx in opportunity_indices:
            if 0 < idx <= len(insights):
                verdict = insights[idx - 1].get("validation", {}).get("verdict", "")
                if verdict == "feasible":
                    feasible_count += 1
        
        opportunity_details = []
        for idx in opportunity_indices:
            if 0 < idx <= len(insights):
                insight = insights[idx - 1]
                opportunity_details.append({
                    "opportunity": insight.get("product_opportunity", ""),
                    "confidence": insight.get("confidence", "medium"),
                    "verdict": insight.get("validation", {}).get("verdict", "unknown"),
                    "reason": insight.get("validation", {}).get("reason", "")
                })
        
        backlog_item = {
            "priority_score": feasible_count * 10 + len(opportunity_indices),  # Weighted score
            "theme": theme_name,
            "summary": summary,
            "opportunity_count": len(opportunity_indices),
            "feasible_count": feasible_count,
            "opportunities": opportunity_details
        }
        backlog.append(backlog_item)
    
    # Sort by priority score descending
    backlog.sort(key=lambda x: x["priority_score"], reverse=True)
    
    return backlog


def display_prioritized_backlog(backlog):
    """
    Display the prioritized opportunity backlog.
    """
    print("\n" + "="*60)
    print("🎯 PRIORITIZED OPPORTUNITY BACKLOG")
    print("="*60)
    
    for rank, item in enumerate(backlog, 1):
        theme = item["theme"]
        summary = item["summary"]
        count = item["opportunity_count"]
        feasible = item["feasible_count"]
        score = item["priority_score"]
        
        print(f"\n#{rank} [{score} pts] {theme.upper()}")
        print(f"    Summary: {summary}")
        print(f"    Total opportunities: {count} | Feasible: {feasible}")
        
        for i, opp in enumerate(item["opportunities"], 1):
            status = "✅" if opp["verdict"] == "feasible" else "⚠️" if opp["verdict"] == "out_of_scope" else "❌"
            confidence = opp["confidence"].upper() if opp["confidence"] else "UNKNOWN"
            
            print(f"    {status} {i}. {opp['opportunity'][:80]}...")
            print(f"       Confidence: {confidence} | Verdict: {opp['verdict']}")


def save_backlog_to_csv(backlog, app_name):
    """
    Save prioritized backlog to CSV.
    """
    data = []
    
    for rank, item in enumerate(backlog, 1):
        for opp in item["opportunities"]:
            row = {
                "rank": rank,
                "theme": item["theme"],
                "theme_summary": item["summary"],
                "opportunity": opp["opportunity"],
                "confidence": opp["confidence"],
                "verdict": opp["verdict"],
                "validation_reason": opp["reason"],
                "priority_score": item["priority_score"]
            }
            data.append(row)
    
    df_backlog = pd.DataFrame(data)
    filename = f"{app_name}_backlog.csv"
    df_backlog.to_csv(filename, index=False, encoding="utf-8")
    print(f"✅ Backlog saved to: {filename}")
    return filename


def generate_executive_summary(insights, backlog, app_name):
    """
    Generate a Gemini executive summary of top 3 opportunities.
    """
    # Get top 3 opportunities from backlog
    top_3 = []
    for item in backlog[:3]:
        for opp in item["opportunities"][:2]:  # Top 2 per theme
            top_3.append({
                "theme": item["theme"],
                "opportunity": opp["opportunity"],
                "confidence": opp["confidence"],
                "verdict": opp["verdict"]
            })
    
    top_3 = top_3[:3]  # Limit to 3
    
    opportunities_text = "\n".join([
        f"{i+1}. [{opp['theme']}] {opp['opportunity']}"
        for i, opp in enumerate(top_3)
    ])
    
    prompt = f"""You are an executive advisor reviewing product opportunities for {app_name}.

Based on user feedback analysis, here are the top 3 opportunities:

{opportunities_text}

Write a concise executive summary (100-150 words) that:
1. Explains why these 3 are most critical
2. The potential impact if implemented
3. One recommendation for immediate action

Be direct and actionable."""
    
    try:
        response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
        return response.text
    
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return None


def display_executive_summary(summary, app_name):
    """
    Display the executive summary formatted.
    """
    print("\n" + "="*60)
    print("📋 EXECUTIVE SUMMARY")
    print("="*60)
    print(f"\nApp: {app_name}")
    print("\n" + summary)
    print("\n" + "="*60)



st.title("🔍 PM Discovery Tool")
st.subheader("From user reviews to product opportunities")

# ── Filtros ───────────────────────────────────────────────────
app_query = st.text_input(
    "📱 Search App or Paste Play Store URL",
    placeholder="e.g. Strava, Goodreads, or a Play Store link",
    help="Search by app name or paste a Google Play Store URL."
)

search_lang = st.session_state.get("lang", "en")
search_country = st.session_state.get("country", "us")
selected_app_id = ""
selected_app_name = ""

if app_query.strip():
    app_id_from_url = extract_app_id_from_url(app_query)

    if app_id_from_url:
        selected_app = resolve_app_from_url(app_id_from_url, lang=search_lang, country=search_country)
        selected_app_id = selected_app["app_id"]
        selected_app_name = selected_app["title"]
        st.caption(f"Detected app from URL: {selected_app_name} ({selected_app_id})")
    else:
        app_results = search_apps(app_query, lang=search_lang, country=search_country)
        if app_results:
            selected_app_index = st.selectbox(
                "Select app",
                options=range(len(app_results)),
                format_func=lambda index: f"{app_results[index]['title']} ({app_results[index]['developer']})",
            )
            selected_app = app_results[selected_app_index]
            selected_app_id = selected_app["app_id"]
            selected_app_name = selected_app["title"]
            st.caption(f"Selected package: {selected_app_id}")
        else:
            st.warning("No apps found for that search. Try a different name or paste a Play Store URL.")

col1, col2 = st.columns(2)

with col1:
    sort_option = st.selectbox(
        "Sort by",
        options=["Most Relevant", "Most Recent"]
    )

with col2:
    num_reviews = st.number_input(
        "🔢 Number of reviews",
        min_value=5,
        max_value=200,
        value=20,
        step=5
    )

with st.expander("⚙️ Advanced Settings"):
    col1, col2 = st.columns(2)
    with col1:
        lang = st.selectbox(
            "Language",
            ["en", "pt", "es", "fr", "de"],
            index=0,
            key="lang",
        )
    with col2:
        country = st.selectbox(
            "Country",
            ["us", "pt", "br", "gb", "es"],
            index=0,
            key="country",
        )

st.write("Star Rating")
star_cols = st.columns(5)
selected_stars = []

for i, col in enumerate(star_cols):
    star = i + 1
    label = f"{star}★"
    default = star <= 3
    with col:
        if st.checkbox(label, value=default, key=f"star_{star}"):
            selected_stars.append(star)

if st.button("Analyse"):
    if not selected_app_id:
        st.error("Please search for an app and select a result.")
    else:
        # Map sort option
        sort_order = 2 if sort_option == "Most Relevant" else 1
        
        with st.spinner("Fetching reviews and analysing..."):
            # Fetch reviews already filtered by selected star ratings
            st.write(f"📱 Fetching reviews from Google Play for {selected_app_name}...")
            reviews_data = get_reviews(
                selected_app_id,
                num_reviews,
                rating_filter=0,
                sort_order=sort_order,
                selected_ratings=selected_stars if selected_stars else None,
                lang=lang,
                country=country,
            )
            
            st.write(f"✅ Fetched {len(reviews_data)} reviews from Google Play")

            reviews_data_filtered = reviews_data
            if selected_stars:
                st.write(f"✅ Using {len(reviews_data_filtered)} reviews with ratings: {selected_stars}")
            else:
                st.write(f"✅ Using all {len(reviews_data_filtered)} reviews (no rating filter)")
            
            if not reviews_data_filtered:
                st.error(f"❌ No reviews found matching the selected filters. Fetched {len(reviews_data)} reviews total.")
                if reviews_data:
                    available_ratings = set(r['rating'] for r in reviews_data)
                    st.info(f"Available ratings in fetched reviews: {sorted(available_ratings)}")
            else:
                # Get texts for analysis
                filtered_reviews = [r['text'] for r in reviews_data_filtered]

                # Analyze up to the amount selected in the input
                max_to_analyze = min(num_reviews, len(filtered_reviews))
                progress_text = st.empty()
                progress_bar = st.progress(0)

                def update_analysis_progress(completed, total):
                    progress_text.write(f"🤖 Analisadas {completed}/{total} reviews...")
                    progress_bar.progress(completed / total)

                update_analysis_progress(0, max_to_analyze)

                analyzed_pairs = analyze_reviews_concurrently(
                    reviews_data_filtered,
                    selected_app_name,
                    max_reviews=max_to_analyze,
                    progress_callback=update_analysis_progress,
                )
                insights = [pair["insight"] for pair in analyzed_pairs]
                successful_reviews = [pair["review"] for pair in analyzed_pairs]
                
                st.write(f"✅ Analyzed {len(insights)} reviews")
                
                if not insights:
                    st.error("❌ No insights generated. Check the API key and review content.")
                else:
                    # Convert to DataFrame
                    results_df = insights_to_dataframe(insights, successful_reviews)
                    
                    st.success("✅ Analysis complete!")
                    st.dataframe(results_df)

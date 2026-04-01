import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google_play_scraper import reviews, Sort
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)


def get_reviews(app_name, count=50, rating_filter=0, sort_order=1, selected_ratings=None):
    """
    Fetch reviews from Google Play and filter by rating and sort order.
    Returns a list of review dicts with 'text' and 'rating'.
    """
    ratings_to_filter = selected_ratings if selected_ratings else ([] if rating_filter == 0 else [rating_filter])
    fetch_count = count * 3 if ratings_to_filter else count

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
        
        sort_by = sort_map[sort_order]
        
        # Fetch more reviews when filtering by ratings to improve chance of reaching target count
        reviews_data, continuation_token = reviews(app_name, count=fetch_count, sort=sort_by, lang="en", country="US")
        
        # Filter reviews by rating
        filtered_reviews = []
        for review in reviews_data:
            rating = review.get("score", 0)
            if not ratings_to_filter or rating in ratings_to_filter:
                review_date = review.get("at")
                filtered_reviews.append({
                    'text': review.get("content", ""),
                    'rating': rating,
                    'date': review_date.isoformat() if review_date else "N/A"
                })

            if len(filtered_reviews) >= count:
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
        print(f"   Sort: {sort_names[sort_order]}")
        
        return filtered_reviews
    
    except Exception as e:
        print(f"❌ Error fetching reviews: {e}")
        return []

def analyze_review(review_text, app_name):
    """
    Analyze a single review using Gemini as a Senior Product Manager.
    Returns insight as JSON.
    """
    prompt = f"""
You are a senior Product Manager with 20 years of experience conducting user research.

Your job is to read a user review and extract a structured product insight, ready to be shared with a product team.

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

  "confidence": "high, medium, or low - based on how clearly the review supports this insight"
}}

Rules:
- Maximum 20 words per field
- No technical jargon
- Write as if briefing a developer and a designer simultaneously
- Be consistent with theme naming across reviews
- JSON only, no extra text
"""
    
    try:
        response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
        # Parse JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            # Find closing ```
            parts = response_text.split("```")
            if len(parts) >= 2:
                response_text = parts[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
        
        insight = json.loads(response_text)

        # Normalize field names so downstream code can use consistent keys.
        # Gemini returns: problem_statement, insight, opportunity
        # Existing pipeline expects: root_problem, user_gap, product_opportunity
        if "root_problem" not in insight and "problem_statement" in insight:
            insight["root_problem"] = insight.get("problem_statement")
        if "user_gap" not in insight and "insight" in insight:
            insight["user_gap"] = insight.get("insight")
        if "product_opportunity" not in insight and "opportunity" in insight:
            insight["product_opportunity"] = insight.get("opportunity")

        return insight
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"   Response was: {response_text[:200]}")
        return None
    except Exception as e:
        print(f"❌ Error analyzing review: {e}")
        return None


def validate_opportunity(product_opportunity, app_name):
    """
    Validate if a product opportunity is feasible, in-scope, and new.
    Returns validation result as JSON.
    """
    prompt = f"""Given this product opportunity for {app_name}:

"{product_opportunity}"

Evaluate:
1. Is this technically feasible for this type of app?
2. Is it within the app's current scope?
3. Does it already exist as a feature?

Respond in JSON:
{{
  "verdict": "feasible / out_of_scope / already_exists",
  "reason": "one sentence explanation"
}}

Be strict. Only mark as feasible if genuinely new and buildable.
Only respond with valid JSON, no other text."""
    
    try:
        response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        validation = json.loads(response_text)
        return validation
    
    except Exception as e:
        print(f"❌ Error validating opportunity: {e}")
        return None


def analyze_multiple_reviews(reviews_list, app_name, max_reviews=10):
    """
    Analyze multiple reviews and aggregate insights with validation.
    Returns list of insights with validation verdicts.
    """
    print(f"\n🤖 Analyzing {min(len(reviews_list), max_reviews)} reviews...")
    
    insights = []
    
    for i, review in enumerate(reviews_list[:max_reviews]):
        print(f"   Processing review {i+1}/{min(len(reviews_list), max_reviews)}...")
        insight = analyze_review(review, app_name)
        
        if insight:
            # Validate the product opportunity
            product_opportunity = insight.get("product_opportunity", "")
            validation = validate_opportunity(product_opportunity, app_name)
            
            if validation:
                insight["validation"] = validation
        
            insights.append(insight)
    
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
app_name = st.text_input(
    "📱 App Name",
    placeholder="ex: com.strava, com.goodreads.app",
    help="Enter the app package name from Google Play. You can find it in the app URL on Play Store (e.g., play.google.com/store/apps/details?id=com.strava)."
)

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
    if not app_name.strip():
        st.error("Please enter an app name.")
    else:
        # Map sort option
        sort_order = 2 if sort_option == "Most Relevant" else 1
        
        with st.spinner("Fetching reviews and analysing..."):
            # Fetch reviews already filtered by selected star ratings
            st.write("📱 Fetching reviews from Google Play...")
            reviews_data = get_reviews(
                app_name,
                num_reviews,
                rating_filter=0,
                sort_order=sort_order,
                selected_ratings=selected_stars if selected_stars else None,
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

                # Show some reviews as debug
                st.write(f"📝 Sample review text: {filtered_reviews[0][:100]}...")

                # Analyze up to the amount selected in the input
                max_to_analyze = min(num_reviews, len(filtered_reviews))
                st.write(f"🤖 Analyzing {max_to_analyze} reviews...")

                insights = []
                for review in filtered_reviews[:max_to_analyze]:
                    insight = analyze_review(review, app_name)

                    if insight:
                        # Validate the product opportunity
                        product_opportunity = insight.get("product_opportunity", "")
                        validation = validate_opportunity(product_opportunity, app_name)

                        if validation:
                            insight["validation"] = validation

                        insights.append(insight)
                
                st.write(f"✅ Analyzed {len(insights)} reviews")
                
                if not insights:
                    st.error("❌ No insights generated. Check the API key and review content.")
                else:
                    # Convert to DataFrame
                    results_df = insights_to_dataframe(insights, reviews_data_filtered[:len(insights)])
                    
                    st.success("✅ Analysis complete!")
                    st.dataframe(results_df)

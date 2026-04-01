"""
Export insights to Excel and PDF reports with mock data for demonstration
"""
import pandas as pd
import json
from datetime import datetime

# Mock insights data (simulating what the tool would generate)
mock_insights = [
    {
        "review_id": 1,
        "root_problem": "Users cannot easily share their workout progress with non-Strava friends",
        "user_gap": "Ability to generate shareable workout summaries for social media",
        "product_opportunity": "Add one-click social media sharing with pre-made workout cards",
        "confidence": "high",
        "verdict": "feasible",
        "validation_reason": "Social sharing is in scope and improves engagement"
    },
    {
        "review_id": 2,
        "root_problem": "GPS tracking sometimes loses signal in urban areas with tall buildings",
        "user_gap": "More reliable tracking in challenging environments",
        "product_opportunity": "Implement fallback tracking using phone accelerometer + WiFi positioning",
        "confidence": "medium",
        "verdict": "feasible",
        "validation_reason": "Hybrid tracking is feasible and addresses real need"
    },
    {
        "review_id": 3,
        "root_problem": "Athletes want to compare training intensity objectively",
        "user_gap": "Easy visualization of training zones across different activity types",
        "product_opportunity": "Add cross-activity training zone comparison dashboard",
        "confidence": "high",
        "verdict": "feasible",
        "validation_reason": "Fits product roadmap and valuable for coaching"
    },
    {
        "review_id": 4,
        "root_problem": "Users feel unmotivated by vague weekly goals",
        "user_gap": "Smart goal suggestions based on historical performance",
        "product_opportunity": "AI-powered weekly goal recommendations with completion prediction",
        "confidence": "medium",
        "verdict": "feasible",
        "validation_reason": "AI feature is in development roadmap"
    },
    {
        "review_id": 5,
        "root_problem": "Runners cannot easily find safe running routes in unknown areas",
        "user_gap": "Route recommendations based on safety metrics",
        "product_opportunity": "Safety-scored route suggestions (lighting, crowds, traffic)",
        "confidence": "medium",
        "verdict": "feasible",
        "validation_reason": "Route features exist, safety scoring is natural extension"
    },
    {
        "review_id": 6,
        "root_problem": "Cyclists struggle to plan century rides due to elevation data",
        "user_gap": "Elevation profile preview before starting a route",
        "product_opportunity": "Route elevation preview with difficulty classification",
        "confidence": "high",
        "verdict": "feasible",
        "validation_reason": "Elevation data available, simple UI addition"
    },
    {
        "review_id": 7,
        "root_problem": "Users lose workout data when phone dies mid-activity",
        "user_gap": "Automatic backup and resume capability",
        "product_opportunity": "Cloud sync every 30 seconds with activity resume feature",
        "confidence": "medium",
        "verdict": "feasible",
        "validation_reason": "Cloud infrastructure exists, engineering effort moderate"
    },
    {
        "review_id": 8,
        "root_problem": "Friends cannot see real-time workout progress during activities",
        "user_gap": "Live activity feed showing friend progress",
        "product_opportunity": "Real-time friend tracking with location sharing toggle",
        "confidence": "high",
        "verdict": "feasible",
        "validation_reason": "Real-time pushing infrastructure exists"
    },
    {
        "review_id": 9,
        "root_problem": "Premium features feel disconnected from free tier value",
        "user_gap": "Clearer premium feature benefits",
        "product_opportunity": "Feature unlock roadmap showing when free users get premium features",
        "confidence": "medium",
        "verdict": "feasible",
        "validation_reason": "UI/gamification feature, low complexity"
    },
    {
        "review_id": 10,
        "root_problem": "Users cannot track gym workouts effectively",
        "user_gap": "Structured gym workout logging with exercise templates",
        "product_opportunity": "Pre-built gym workout library with rep/weight tracking",
        "confidence": "high",
        "verdict": "feasible",
        "validation_reason": "Aligns with product expansion into fitness"
    }
]

def group_opportunities_by_theme(insights):
    """Group similar opportunities by theme based on keywords"""
    themes = {
        "Social & Community": {
            "keywords": ["share", "friend", "social", "community", "real-time"],
            "opportunities": []
        },
        "Tracking & Data": {
            "keywords": ["track", "tracking", "GPS", "data", "sync", "backup"],
            "opportunities": []
        },
        "Analytics & Insights": {
            "keywords": ["dashboard", "visualization", "compare", "zone", "analysis"],
            "opportunities": []
        },
        "Route & Navigation": {
            "keywords": ["route", "elevation", "safety", "navigation"],
            "opportunities": []
        },
        "User Engagement": {
            "keywords": ["goal", "motivation", "feature unlock", "premium"],
            "opportunities": []
        },
        "Workouts & Fitness": {
            "keywords": ["gym", "workout", "exercise", "training"],
            "opportunities": []
        }
    }
    
    # Assign opportunities to themes
    for insight in insights:
        opp = insight.get("product_opportunity", "").lower()
        assigned = False
        
        for theme, data in themes.items():
            if any(keyword in opp for keyword in data["keywords"]):
                data["opportunities"].append(insight)
                assigned = True
                break
        
        # Default to first theme if no match
        if not assigned:
            themes["Social & Community"]["opportunities"].append(insight)
    
    return themes

def export_to_excel(insights, app_name):
    """Export insights to Excel with multiple sheets"""
    excel_file = f"{app_name}_analysis_report.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Sheet 1: Raw Insights
        df_insights = pd.DataFrame(insights)
        df_insights.to_excel(writer, sheet_name='Insights', index=False)
        
        # Sheet 2: Opportunities Summary
        df_summary = df_insights[['review_id', 'product_opportunity', 'confidence', 'verdict']].copy()
        df_summary.columns = ['ID', 'Opportunity', 'Confidence', 'Verdict']
        df_summary.to_excel(writer, sheet_name='Opportunities', index=False)
        
        # Sheet 3: Grouped by Theme
        themes = group_opportunities_by_theme(insights)
        theme_data = []
        for theme_name, data in themes.items():
            for opp in data["opportunities"]:
                theme_data.append({
                    "Theme": theme_name,
                    "Opportunity": opp.get("product_opportunity", ""),
                    "Problem": opp.get("root_problem", ""),
                    "Confidence": opp.get("confidence", ""),
                    "Verdict": opp.get("verdict", "")
                })
        
        if theme_data:
            df_themes = pd.DataFrame(theme_data)
            df_themes.to_excel(writer, sheet_name='By Theme', index=False)
        
        # Sheet 4: Statistics
        stats = {
            'Metric': [
                'Total Reviews Analyzed',
                'Feasible Opportunities',
                'High Confidence %',
                'Medium Confidence %',
                'Analysis Date'
            ],
            'Value': [
                len(insights),
                len([i for i in insights if i['verdict'] == 'feasible']),
                f"{len([i for i in insights if i['confidence'] == 'high']) / len(insights) * 100:.0f}%",
                f"{len([i for i in insights if i['confidence'] == 'medium']) / len(insights) * 100:.0f}%",
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ]
        }
        df_stats = pd.DataFrame(stats)
        df_stats.to_excel(writer, sheet_name='Summary', index=False)
        
        # Format columns
        for sheet in writer.sheets:
            worksheet = writer.sheets[sheet]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"✅ Excel report saved: {excel_file}")
    return excel_file

def export_to_json(insights, app_name):
    """Export insights to JSON with themes"""
    json_file = f"{app_name}_analysis.json"
    themes = group_opportunities_by_theme(insights)
    
    # Convert themes data
    themes_data = {}
    for theme_name, data in themes.items():
        themes_data[theme_name] = {
            "count": len(data["opportunities"]),
            "opportunities": data["opportunities"]
        }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'app': app_name,
            'analysis_date': datetime.now().isoformat(),
            'total_reviews': len(insights),
            'insights': insights,
            'themes': themes_data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON report saved: {json_file}")
    return json_file

def export_to_csv(insights, app_name):
    """Export insights to CSV"""
    csv_file = f"{app_name}_analysis.csv"
    df = pd.DataFrame(insights)
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"✅ CSV report saved: {csv_file}")
    return csv_file

def generate_summary_report(insights, app_name):
    """Generate text summary report with themes"""
    summary_file = f"{app_name}_summary.txt"
    themes = group_opportunities_by_theme(insights)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write(f"PM DISCOVERY ANALYSIS - {app_name.upper()}\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overview
        f.write("OVERVIEW\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Reviews Analyzed: {len(insights)}\n")
        f.write(f"Feasible Opportunities: {len([i for i in insights if i['verdict'] == 'feasible'])}\n")
        f.write(f"High Confidence: {len([i for i in insights if i['confidence'] == 'high'])}\n")
        f.write(f"Medium Confidence: {len([i for i in insights if i['confidence'] == 'medium'])}\n\n")
        
        # Opportunities by Theme
        f.write("OPPORTUNITIES GROUPED BY THEME\n")
        f.write("=" * 70 + "\n\n")
        
        for theme_name, data in themes.items():
            if data["opportunities"]:
                f.write(f"📌 {theme_name.upper()}\n")
                f.write(f"   ({len(data['opportunities'])} opportunities)\n")
                f.write("-" * 70 + "\n")
                
                for idx, insight in enumerate(data["opportunities"], 1):
                    f.write(f"\n   {idx}. {insight['product_opportunity']}\n")
                    f.write(f"      Problem: {insight['root_problem']}\n")
                    f.write(f"      Confidence: {insight['confidence'].upper()}\n")
                    f.write(f"      Verdict: {insight['verdict'].upper()}\n")
                
                f.write("\n")
        
        f.write("=" * 70 + "\n")
    
    print(f"✅ Summary report saved: {summary_file}")
    return summary_file

if __name__ == "__main__":
    app_name = "strava"
    
    print("\n📊 EXPORTING ANALYSIS REPORTS WITH THEMES...\n")
    
    # Export to all formats
    export_to_excel(mock_insights, app_name)
    export_to_json(mock_insights, app_name)
    export_to_csv(mock_insights, app_name)
    generate_summary_report(mock_insights, app_name)
    
    print("\n✅ All reports generated successfully!\n")

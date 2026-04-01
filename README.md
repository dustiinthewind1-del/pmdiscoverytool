# PM Discovery Tool

Turn Google Play reviews into product opportunities using Gemini AI. Built for Product Managers who want faster, structured discovery.

## 🚀 Overview

PM Discovery Tool is a web application that automates user feedback analysis. Using Google Gemini, it extracts structured insights from Google Play reviews, identifies problems and opportunities, and helps prioritize product improvements.

### ✨ Key Features

- **📱 Review Collection**: Fetches Google Play reviews with rating and sorting filters
- **🤖 AI Analysis**: Uses Gemini to extract structured insights from each review
- **✅ Opportunity Validation**: Checks whether opportunities are feasible and in scope
- **📊 Theme Grouping**: Organizes similar opportunities by category
- **🎯 Prioritized Backlog**: Builds a priority list based on frequency and feasibility
- **📋 Executive Summary**: Generates a concise executive summary of top opportunities
- **💾 Export**: Saves outputs as JSON and CSV

## 🛠️ Tech Stack

- **Python 3.8+**
- **Streamlit** - Web interface
- **Google Play Scraper** - Review collection
- **Google Gemini AI** - Text analysis
- **Pandas** - Data processing
- **python-dotenv** - Environment variable management

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Google Cloud account with Gemini API enabled
- Gemini API key

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dustiinthewind1-del/pmdiscoverytool.git
   cd pmdiscoverytool
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## 🚀 Usage

### Run the App

```bash
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`.

### User Flow

1. **Enter the app package name** (e.g., `com.strava`, `com.goodreads.app`)
2. **Configure filters:**
   - Sort type (Most Relevant, Most Recent)
   - Number of reviews (5-200)
   - Desired ratings (1-5 stars)
3. **Click "Analyse"**
4. **Wait for processing** - the tool will:
   - Fetch reviews
   - Analyze each review with AI
   - Validate opportunities
   - Show results in a table

### Example

To analyze Strava reviews:
- App name: `com.strava`
- Reviews: 20
- Ratings: 1, 2, 3 stars
- Sort: Most Relevant

## 📁 Project Structure

```
pmdiscoverytool/
├── main.py                 # Main Streamlit application
├── export_report.py        # Report generator (CLI)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment config template
├── .gitignore              # Ignored files
├── README.md               # This file
└── strava_*                # Sample output files (CSV, JSON, XLSX)
```

## 🔧 Detailed Functionality

### Review Analysis

Each review is analyzed by Gemini with a structured prompt that extracts:
- **Theme**: Problem category (2-3 words)
- **Problem Statement**: What is broken from the user's perspective
- **Insight**: Deeper reason behind the complaint
- **Opportunity**: Specific, buildable solution
- **Acceptance Criteria**: How success is measured
- **Priority Signal**: High/Medium/Low impact
- **Confidence**: High/Medium/Low confidence in the insight

### Opportunity Validation

Each opportunity is validated for:
- **Technical Feasibility**: Can this be built?
- **Scope Fit**: Is it within current app scope?
- **Novelty**: Does this already exist?

### Theme Grouping

Opportunities are automatically grouped by similar themes using AI.

### Prioritized Backlog

Creates a ranked list based on:
- Mention frequency
- Opportunity feasibility
- Weighted scoring

## 📊 Analysis Outputs

### Generated Files
- `{app_name}_insights.json` - Structured insights
- `{app_name}_insights.csv` - Tabular data
- `{app_name}_backlog.csv` - Prioritized backlog

### Output Formats
- **JSON**: Structured data for integrations and processing
- **CSV**: Spreadsheet-friendly format for manual analysis
- **Web UI**: Interactive Streamlit visualization

## 🔐 API Configuration

### Get a Gemini Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key into `.env`

### Security
- Never commit your real API key
- Always use environment variables
- `.gitignore` is already set up to ignore `.env`

## 🐛 Troubleshooting

### Common Issues

**API key error:**
- Check if the key is correct in `.env`
- Confirm Gemini API is enabled

**No reviews found:**
- Verify the app package name
- Try reducing the number of reviews
- Change rating filters

**Dependency errors:**
- Ensure you are using Python 3.8+
- Reinstall dependencies: `pip install -r requirements.txt`

### Debug Mode

For more execution details, check the terminal where Streamlit is running.

## 🤝 Contributing

Contributions are welcome. To contribute:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

### Improvement Ideas
- Support for more app stores (App Store, etc.)
- More advanced sentiment analysis
- Metrics dashboard
- Integration with PM tools (Jira, Linear, etc.)

## 📄 License

This project is licensed under the MIT License. See `LICENSE` for details.

## 🙏 Acknowledgements

- Google Gemini for AI capabilities
- Google Play Scraper for data collection
- Streamlit for the web framework
- Python community for excellent packages

---

**Built with ❤️ for Product Managers who want to accelerate product discovery.**

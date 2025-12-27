# Pricing Model

Here is the file layout:

```
pricingmodel/
├── src/                    # Python source files
│   ├── creator_registry.py # Creator registry and matching logic
│   ├── calculate_costs.py  # Financial model calculations
│   ├── analyze_videos.py  # Video analysis and statistics
│   └── export_dashboard_data.py # Generate JSON data for dashboard
├── api/                    # Vercel serverless functions
│   └── process_csv.py     # API endpoint to process CSV uploads
├── data/                   # Data files (CSV and JSON)
│   ├── videos_*.csv       # Input video data (not committed)
│   ├── creator_statistics.csv # Generated creator statistics
│   └── model*.json        # Generated model data for dashboard
├── web/                    # Web dashboard
│   └── dashboard.html     # Interactive dashboard UI with CSV upload
├── start_dashboard.py     # Start the dashboard server
├── vercel.json            # Vercel deployment configuration
└── README.md              # This file
```

Here is how to start the app:

**Local Development:**
```bash
python3 start_dashboard.py
```

This will:
1. Generate all model data files
2. Start a local web server
3. Open the dashboard in your browser

The dashboard will be available at: `http://localhost:8000/web/dashboard.html`

**Using CSV Upload:**
- Upload your viral.app CSV file directly through the dashboard interface
- No need to commit CSV data to the repository
- Data is processed on-the-fly via the API endpoint


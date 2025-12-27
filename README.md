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
├── data/                   # Data files (not committed to git)
│   └── (generated from CSV uploads, excluded via .gitignore)
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
1. Start a local web server
2. Open the dashboard in your browser

The dashboard will be available at: `http://localhost:8000/web/dashboard.html`

**Using CSV Upload:**
- Upload your viral.app CSV file directly through the dashboard interface
- Data is processed on-the-fly and automatically generates all model calculations
- No data files are stored or committed to the repository
- CSV upload is the only way to generate dashboard data


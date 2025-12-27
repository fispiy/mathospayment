# Pricing Model

Here is the file layout:

```
pricingmodel/
├── src/                    # Python source files
│   ├── creator_registry.py # Creator registry and matching logic
│   ├── calculate_costs.py  # Financial model calculations
│   ├── analyze_videos.py  # Video analysis and statistics
│   └── export_dashboard_data.py # Generate JSON data for dashboard
├── data/                   # Data files (not committed to git)
│   └── (generated JSON files, excluded via .gitignore)
├── web/                    # Web dashboard
│   └── dashboard.html     # Interactive dashboard UI
├── start_dashboard.py     # Start the dashboard server
└── README.md              # This file
```

Here is how to start the app:

```bash
python3 start_dashboard.py
```

This will:
1. Generate all model data files from your CSV data
2. Start a local web server on port 8000
3. Open the dashboard in your browser

The dashboard will be available at: `http://localhost:8000/web/dashboard.html`

**To update data:**
1. Place your CSV file in the `data/` folder
2. Update the CSV path in `src/analyze_videos.py` if needed
3. Run `python3 start_dashboard.py` to regenerate data and view dashboard

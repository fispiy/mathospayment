#!/usr/bin/env python3
"""
Start the financial model dashboard.
Generates data and opens the dashboard in your browser.
"""

import webbrowser
import http.server
import socketserver
import os
import sys
from pathlib import Path

def main():
    # Add src to path for imports
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root / 'src'))
    
    # Note: Data files are now generated via CSV upload in the dashboard
    # No need to generate them upfront
    print("Dashboard server starting...")
    print("Note: Upload a CSV file through the dashboard to generate data.\n")
    
    # Start web server
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Change to the project root directory
    os.chdir(project_root)
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/web/dashboard.html"
        print("="*60)
        print("Financial Model Dashboard")
        print("="*60)
        print(f"\nDashboard is running at: {url}")
        print(f"Project root: {project_root}")
        print("\nPress Ctrl+C to stop the server\n")
        print("="*60)
        
        # Try to open browser automatically
        try:
            webbrowser.open(url)
        except:
            print(f"Please open your browser and go to: {url}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")

if __name__ == '__main__':
    main()


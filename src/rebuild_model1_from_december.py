#!/usr/bin/env python3
"""
Rebuild Model 1 from scratch based on December spreadsheet data.
Logic:
1. Parse December spreadsheet
2. Identify paid videos (marked "Paid")
3. Group videos: if links below a paid video have same date/creator but no "Paid", they're same video on different platforms
4. Sum views across platforms for each unique video
5. Calculate totals: base payment per video + bonus based on 14-day sum of views
"""

import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime

def parse_views(view_str):
    """Parse view count string (may contain commas)."""
    if not view_str:
        return 0
    try:
        return int(str(view_str).replace(',', ''))
    except (ValueError, TypeError):
        return 0

def parse_amount(amount_str):
    """Parse payment amount string."""
    if not amount_str:
        return 0
    try:
        return float(str(amount_str).replace(',', ''))
    except (ValueError, TypeError):
        return 0

def parse_december_data(csv_file):
    """Parse December data and group videos correctly."""
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 9:
                rows.append(row)
    
    # Group videos by creator and date
    # Structure: Paid video + entries below with same date/creator (no Paid) = same video
    creator_videos = defaultdict(list)
    
    i = 0
    while i < len(rows):
        row = rows[i]
        date = row[0].strip() if len(row) > 0 else ''
        creator = row[1].strip() if len(row) > 1 else ''
        paid = row[8].strip().lower() if len(row) > 8 else ''
        
        if not creator or not date:
            i += 1
            continue
        
        # If this is a paid video, collect it and any related entries below
        if paid == 'paid':
            video_group = []
            
            # Add the paid entry
            amount = parse_amount(row[7].strip() if len(row) > 7 else '')
            views = parse_views(row[6].strip() if len(row) > 6 else '')
            platform = row[4].strip() if len(row) > 4 else ''
            link = row[3].strip() if len(row) > 3 else ''
            
            video_group.append({
                'date': date,
                'creator': creator,
                'amount': amount,
                'views': views,
                'platform': platform,
                'link': link,
                'paid': True
            })
            
            # Look ahead for related entries (same date, same creator, no Paid)
            j = i + 1
            while j < len(rows):
                next_row = rows[j]
                next_date = next_row[0].strip() if len(next_row) > 0 else ''
                next_creator = next_row[1].strip() if len(next_row) > 1 else ''
                next_paid = next_row[8].strip().lower() if len(next_row) > 8 else ''
                
                # If same date and creator, and not paid, it's the same video on different platform
                if next_date == date and next_creator == creator and next_paid != 'paid':
                    next_views = parse_views(next_row[6].strip() if len(next_row) > 6 else '')
                    next_platform = next_row[4].strip() if len(next_row) > 4 else ''
                    next_link = next_row[3].strip() if len(next_row) > 3 else ''
                    
                    video_group.append({
                        'date': date,
                        'creator': creator,
                        'amount': 0,  # Not paid separately
                        'views': next_views,
                        'platform': next_platform,
                        'link': next_link,
                        'paid': False
                    })
                    j += 1
                else:
                    # Different date or creator, stop grouping
                    break
            
            # Sum views across all platforms for this unique video
            total_views = sum(v['views'] for v in video_group)
            payment_amount = video_group[0]['amount']  # Payment is per unique video
            
            creator_videos[creator].append({
                'date': date,
                'payment': payment_amount,
                'total_views': total_views,
                'platforms': [v['platform'] for v in video_group],
                'links': [v['link'] for v in video_group]
            })
            
            i = j  # Skip processed rows
        else:
            i += 1
    
    return creator_videos

def calculate_bonus(total_views):
    """Calculate bonus based on 14-day sum of views."""
    if total_views >= 5000000:
        return 3000.0
    elif total_views >= 3000000:
        return 2000.0
    elif total_views >= 1000000:
        return 1200.0
    elif total_views >= 500000:
        return 500.0
    elif total_views >= 250000:
        return 200.0
    elif total_views >= 50000:
        return 150.0
    elif total_views >= 20000:
        return 35.0
    else:
        return 0.0

def calculate_model1_from_december():
    """Calculate Model 1 from December data."""
    data_dir = Path(__file__).parent.parent / 'data'
    december_csv = data_dir / 'December Data - Sheet1.csv'
    
    print("Parsing December data...")
    creator_videos = parse_december_data(december_csv)
    
    print(f"\nFound {len(creator_videos)} creators")
    print("\n" + "="*80)
    print("MODEL 1 CALCULATION FROM DECEMBER DATA")
    print("="*80)
    print(f"{'Creator':<30} {'Videos':<10} {'Total Views':<15} {'Base Payment':<15} {'Bonus':<15} {'Total':<15}")
    print("-"*80)
    
    results = []
    total_base = 0
    total_bonus = 0
    total_cost = 0
    
    for creator in sorted(creator_videos.keys()):
        videos = creator_videos[creator]
        total_payment = sum(v['payment'] for v in videos)
        total_views = sum(v['total_views'] for v in videos)
        bonus = calculate_bonus(total_views)
        total = total_payment + bonus
        
        results.append({
            'creator': creator,
            'videos': len(videos),
            'total_views': total_views,
            'base_payment': total_payment,
            'bonus': bonus,
            'total': total
        })
        
        total_base += total_payment
        total_bonus += bonus
        total_cost += total
        
        print(f"{creator:<30} {len(videos):<10} {total_views:<15,} ${total_payment:<14,.2f} ${bonus:<14,.2f} ${total:<14,.2f}")
    
    print("-"*80)
    print(f"{'TOTALS':<30} {sum(r['videos'] for r in results):<10} {sum(r['total_views'] for r in results):<15,} "
          f"${total_base:<14,.2f} ${total_bonus:<14,.2f} ${total_cost:<14,.2f}")
    print("="*80)
    
    # Verify key creators - BASE PAYMENTS should match spreadsheet totals
    print("\nVERIFICATION (Base Payments from Spreadsheet):")
    jasper_result = next((r for r in results if 'studiosjamen' in r['creator'].lower() or 'jasper' in r['creator'].lower()), None)
    john_result = next((r for r in results if 'integratingjohn' in r['creator'].lower() or 'john' in r['creator'].lower()), None)
    
    if jasper_result:
        base_match = abs(jasper_result['base_payment'] - 2190) < 1
        print(f"Jasper (studiosjamen):")
        print(f"  Base Payment: ${jasper_result['base_payment']:.2f} {'✓' if base_match else '✗ Expected $2190'}")
        print(f"  Bonus: ${jasper_result['bonus']:.2f}")
        print(f"  Total: ${jasper_result['total']:.2f}")
    else:
        print("Jasper not found!")
    
    if john_result:
        base_match = abs(john_result['base_payment'] - 740) < 1
        print(f"\nJohn (integratingjohn):")
        print(f"  Base Payment: ${john_result['base_payment']:.2f} {'✓' if base_match else '✗ Expected $740'}")
        print(f"  Bonus: ${john_result['bonus']:.2f}")
        print(f"  Total: ${john_result['total']:.2f}")
    else:
        print("John not found!")
    
    return results

if __name__ == "__main__":
    results = calculate_model1_from_december()


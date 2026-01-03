#!/usr/bin/env python3
"""
Update creator_statistics.csv with paid video counts from December data.
This ensures Model 1 matches actual payouts.
"""

import csv
from collections import defaultdict
from pathlib import Path

def count_paid_videos_from_december():
    """Count paid videos and calculate total base payment per creator from December data."""
    data_dir = Path(__file__).parent.parent / 'data'
    december_csv = data_dir / 'December Data - Sheet1.csv'
    
    # Map creator names from December data to standardized names
    creator_mapping = {
        'integratingjohn': 'John Sellers',
        'Cary-(mathos-official)': 'Cary',
        # Add more mappings as needed
    }
    
    creator_paid_counts = defaultdict(int)
    creator_base_payments = defaultdict(float)  # Total base payment amount
    
    with open(december_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 9:
                continue
            
            creator = row[1].strip() if len(row) > 1 else ''
            paid = row[8].strip().lower() if len(row) > 8 else ''
            amount_str = row[7].strip() if len(row) > 7 else ''
            
            if paid == 'paid' and creator:
                # Map to standardized name
                standardized_name = creator_mapping.get(creator, creator)
                creator_paid_counts[standardized_name] += 1
                
                # Sum up base payment amounts
                try:
                    amount = float(amount_str.replace(',', '')) if amount_str else 0
                    creator_base_payments[standardized_name] += amount
                except (ValueError, TypeError):
                    pass
    
    return creator_paid_counts, creator_base_payments

def update_creator_statistics():
    """Update creator_statistics.csv with paid video counts and base payments."""
    data_dir = Path(__file__).parent / '..' / 'data'
    stats_file = data_dir / 'creator_statistics.csv'
    
    # Get paid video counts and base payments
    paid_counts, base_payments = count_paid_videos_from_december()
    
    # Read existing statistics
    creators = []
    with open(stats_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            creator_name = row['creator_name']
            # Add paid video count if available
            paid_count = None
            base_payment = None
            
            if creator_name in paid_counts:
                paid_count = paid_counts[creator_name]
                base_payment = base_payments.get(creator_name, 0)
            else:
                # Try to find match (case insensitive, partial match)
                for paid_creator, count in paid_counts.items():
                    if creator_name.lower() == paid_creator.lower() or \
                       creator_name.lower() in paid_creator.lower() or \
                       paid_creator.lower() in creator_name.lower():
                        paid_count = count
                        base_payment = base_payments.get(paid_creator, 0)
                        break
            
            if paid_count is None:
                paid_count = row.get('instagram_videos', '0')  # Default to Instagram videos
                base_payment = 0
            
            row['paid_videos'] = paid_count
            row['base_payment'] = base_payment
            creators.append(row)
    
    # Add paid_videos and base_payment to fieldnames if not present
    if 'paid_videos' not in fieldnames:
        fieldnames = list(fieldnames) + ['paid_videos']
    if 'base_payment' not in fieldnames:
        fieldnames = list(fieldnames) + ['base_payment']
    
    # Write updated statistics
    with open(stats_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(creators)
    
    print(f"Updated creator_statistics.csv with paid video counts and base payments")
    john_paid = paid_counts.get('John Sellers', paid_counts.get('integratingjohn', 0))
    john_base = base_payments.get('John Sellers', base_payments.get('integratingjohn', 0))
    print(f"John Sellers: {john_paid} paid videos, ${john_base:.2f} base payment")

if __name__ == "__main__":
    update_creator_statistics()


#!/usr/bin/env python3
"""
Parse newcreators.txt and add new creators to the creator registry.
"""

from pathlib import Path

def parse_newcreators_file(file_path):
    """Parse the newcreators.txt file and return creator data in the same format as CREATOR_DATA."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    creators_data = []
    current_creator = None
    current_creator_name = None
    
    for line in lines:
        line = line.rstrip('\n')
        parts = line.split('\t')
        parts = [p.strip() for p in parts]
        
        # Check if this is a creator name line (first non-empty part is not an account type)
        account_types = ['Contact account', 'Mathos Ins', 'Mathos TT', 'Mathos YT']
        
        if parts and parts[0] and parts[0] not in account_types:
            # This is a new creator line
            if current_creator_name:
                # Save previous creator
                creators_data.append((current_creator_name, current_creator))
            
            current_creator_name = parts[0]
            current_creator = [line]
        elif parts and parts[0] in account_types:
            # This is an account entry
            if current_creator_name:
                current_creator.append(line)
        elif not parts[0] and current_creator_name:
            # Empty line - might be separator, keep current creator
            pass
    
    # Add last creator
    if current_creator_name:
        creators_data.append((current_creator_name, current_creator))
    
    return creators_data

def format_creator_data(creators_data):
    """Format creator data into the CREATOR_DATA format."""
    formatted = []
    for creator_name, creator_lines in creators_data:
        formatted.append('\n'.join(creator_lines))
        formatted.append('')  # Empty line between creators
    
    return '\n'.join(formatted)

if __name__ == '__main__':
    newcreators_file = Path(__file__).parent.parent / 'januaryinfo' / 'newcreators.txt'
    creators_data = parse_newcreators_file(newcreators_file)
    
    print("Found creators:")
    for name, lines in creators_data:
        print(f"  {name}: {len(lines)} lines")
    
    formatted = format_creator_data(creators_data)
    print("\nFormatted data:")
    print(formatted)


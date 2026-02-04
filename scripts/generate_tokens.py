#!/usr/bin/env python3
"""
Generate authentication tokens for Android course students
Creates a JSON file mapping NetID to unique tokens
"""

import json
import secrets
import sys
from pathlib import Path

TOKEN_FILE = '/scratch/android_course/tokens/tokens.json'
TOKEN_LENGTH = 32  # 256-bit token


def generate_token():
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(TOKEN_LENGTH)


def load_tokens():
    """Load existing tokens"""
    token_file = Path(TOKEN_FILE)
    if token_file.exists():
        with open(token_file, 'r') as f:
            return json.load(f)
    return {}


def save_tokens(tokens):
    """Save tokens to file"""
    Path(TOKEN_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)
    print(f"Tokens saved to {TOKEN_FILE}")


def add_student(netid):
    """Add a new student or regenerate token"""
    tokens = load_tokens()
    
    if netid in tokens:
        print(f"Student {netid} already exists. Regenerating token...")
    
    token = generate_token()
    tokens[netid] = token
    save_tokens(tokens)
    
    print(f"\nStudent added: {netid}")
    print(f"Token: {token}")
    print(f"\nProvide this token to the student privately.")


def remove_student(netid):
    """Remove a student's token"""
    tokens = load_tokens()
    
    if netid not in tokens:
        print(f"Student {netid} not found")
        return
    
    del tokens[netid]
    save_tokens(tokens)
    print(f"Student {netid} removed")


def list_students():
    """List all students (without showing tokens)"""
    tokens = load_tokens()
    
    if not tokens:
        print("No students registered")
        return
    
    print(f"\nRegistered students ({len(tokens)}):")
    for netid in sorted(tokens.keys()):
        print(f"  - {netid}")


def bulk_import(filepath):
    """Import students from a file (one NetID per line)"""
    tokens = load_tokens()
    
    with open(filepath, 'r') as f:
        netids = [line.strip() for line in f if line.strip()]
    
    added = 0
    for netid in netids:
        if netid not in tokens:
            tokens[netid] = generate_token()
            added += 1
    
    save_tokens(tokens)
    
    print(f"\nBulk import complete:")
    print(f"  - Added: {added}")
    print(f"  - Already existed: {len(netids) - added}")
    print(f"  - Total students: {len(tokens)}")


def export_tokens(output_file):
    """Export tokens to CSV for distribution"""
    tokens = load_tokens()
    
    if not tokens:
        print("No tokens to export")
        return
    
    with open(output_file, 'w') as f:
        f.write("NetID,Token\n")
        for netid, token in sorted(tokens.items()):
            f.write(f"{netid},{token}\n")
    
    print(f"Tokens exported to {output_file}")
    print(f"Total students: {len(tokens)}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_tokens.py add <netid>           - Add a student")
        print("  python generate_tokens.py remove <netid>        - Remove a student")
        print("  python generate_tokens.py list                  - List all students")
        print("  python generate_tokens.py bulk <file>           - Import from file")
        print("  python generate_tokens.py export <output.csv>   - Export to CSV")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'add':
        if len(sys.argv) != 3:
            print("Usage: python generate_tokens.py add <netid>")
            sys.exit(1)
        add_student(sys.argv[2])
    
    elif command == 'remove':
        if len(sys.argv) != 3:
            print("Usage: python generate_tokens.py remove <netid>")
            sys.exit(1)
        remove_student(sys.argv[2])
    
    elif command == 'list':
        list_students()
    
    elif command == 'bulk':
        if len(sys.argv) != 3:
            print("Usage: python generate_tokens.py bulk <file>")
            sys.exit(1)
        bulk_import(sys.argv[2])
    
    elif command == 'export':
        if len(sys.argv) != 3:
            print("Usage: python generate_tokens.py export <output.csv>")
            sys.exit(1)
        export_tokens(sys.argv[2])
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()

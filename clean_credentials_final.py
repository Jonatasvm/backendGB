#!/usr/bin/env python3
"""
Final credentials.json cleanup script.
Fixes: BOM, Windows line endings, and literal \n in the private key.
"""
import json
import sys

def clean_credentials(input_file, output_file):
    """Load and clean credentials.json"""
    
    # Read as binary to detect encoding issues
    with open(input_file, 'rb') as f:
        raw_bytes = f.read()
    
    # Remove BOM if present
    if raw_bytes.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
        print("Removing UTF-8 BOM...")
        raw_bytes = raw_bytes[3:]
    
    # Decode to string
    try:
        content = raw_bytes.decode('utf-8')
    except UnicodeDecodeError as e:
        print(f"Error decoding UTF-8: {e}")
        # Try with errors='ignore' to strip invalid bytes
        content = raw_bytes.decode('utf-8', errors='ignore')
        print("Decoded with errors='ignore'")
    
    # Parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    
    # Process private_key: convert literal \n to actual newlines
    if 'private_key' in data:
        private_key = data['private_key']
        # Replace literal \n with actual newlines
        private_key = private_key.replace('\\n', '\n')
        data['private_key'] = private_key
        print(f"Converted private_key literal \\n to actual newlines")
    
    # Write as UTF-8 without BOM, with LF line endings
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=2)
    
    print(f"Cleaned credentials written to: {output_file}")
    
    # Verify
    with open(output_file, 'rb') as f:
        verify_bytes = f.read()
    
    if not verify_bytes.startswith(b'\xef\xbb\xbf'):
        print("✓ No BOM present")
    
    if b'\r\n' not in verify_bytes:
        print("✓ Using Unix line endings (LF)")
    
    if b'\\n' not in verify_bytes:
        print("✓ No literal \\n in file (all converted to actual newlines)")
    
    # Check private key structure
    verify_data = json.loads(verify_bytes.decode('utf-8'))
    pk = verify_data['private_key']
    print(f"✓ Private key starts with: {pk[:30]}")
    print(f"✓ Private key ends with: {pk[-30:]}")
    print(f"✓ Private key length: {len(pk)}")

if __name__ == '__main__':
    input_file = 'credentials.json'
    output_file = 'credentials.json'
    
    print(f"Cleaning {input_file}...")
    clean_credentials(input_file, output_file)
    print("Done!")

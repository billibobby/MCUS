#!/usr/bin/env python3
"""
MCUS Version Update Script
Helps update the version number when releasing updates.
"""

import re
import sys
from pathlib import Path

def update_version_in_file(file_path, old_version, new_version):
    """Update version in a specific file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update version in the file
        updated_content = content.replace(old_version, new_version)
        
        with open(file_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated {file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to update {file_path}: {e}")
        return False

def update_version(new_version):
    """Update version number in all relevant files"""
    print(f"🔄 Updating version to {new_version}")
    
    # Files that contain version information
    files_to_update = [
        'src/update_checker.py',
        'README.md'
    ]
    
    # Current version (update this when you change it)
    current_version = "1.0.0"
    
    success_count = 0
    total_files = len(files_to_update)
    
    for file_path in files_to_update:
        if Path(file_path).exists():
            if update_version_in_file(file_path, current_version, new_version):
                success_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n📊 Updated {success_count}/{total_files} files")
    
    if success_count == total_files:
        print(f"🎉 Version successfully updated to {new_version}")
        print("\nNext steps:")
        print("1. Test your changes")
        print("2. Commit your changes:")
        print(f"   git add .")
        print(f"   git commit -m 'Release version {new_version}'")
        print("3. Create a GitHub release:")
        print(f"   - Tag: v{new_version}")
        print(f"   - Title: MCUS {new_version}")
        print("   - Add release notes")
        print("4. Push to GitHub:")
        print(f"   git push origin main --tags")
    else:
        print("❌ Some files failed to update. Please check manually.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        print("Example: python update_version.py 1.1.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("❌ Invalid version format. Use format: X.Y.Z (e.g., 1.1.0)")
        sys.exit(1)
    
    update_version(new_version)

if __name__ == "__main__":
    main() 
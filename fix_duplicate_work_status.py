"""
Script to fix the duplicate work_status_details initialization in engineer_page.py
This script removes the duplicate initialization that causes work status to not be captured.
"""

def fix_duplicate_initialization():
    file_path = "app/engineer_page.py"
    
    print("Reading engineer_page.py...")
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}")
    
    # Find all occurrences of work_status_details initialization
    work_status_lines = []
    for i, line in enumerate(lines):
        if 'work_status_details = {}' in line:
            work_status_lines.append((i, line.strip()))
            print(f"Found at line {i+1}: {line.strip()}")
    
    if len(work_status_lines) >= 2:
        # We found duplicates - remove the second one (inside the if block)
        first_line, second_line = work_status_lines[0][0], work_status_lines[1][0]
        
        print(f"\n❌ Found duplicate initialization:")
        print(f"   Line {first_line+1}: {work_status_lines[0][1]}")
        print(f"   Line {second_line+1}: {work_status_lines[1][1]}")
        
        # Remove the second occurrence
        fixed_lines = lines[:second_line] + lines[second_line+1:]
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print(f"\n✅ Fixed! Removed duplicate at line {second_line+1}")
        print(f"   Kept initialization at line {first_line+1}")
        print(f"   New total lines: {len(fixed_lines)}")
        
    elif len(work_status_lines) == 1:
        print("\n✅ Only one initialization found - already fixed!")
    else:
        print("\n⚠️  No work_status_details initialization found!")

if __name__ == '__main__':
    fix_duplicate_initialization()

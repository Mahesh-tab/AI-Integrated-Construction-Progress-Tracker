"""
Diagnostic script to check floor-wise data availability
Run this to diagnose why floor-wise metrics aren't showing
"""
import sqlite3
import sys

def diagnose_floor_data():
    print("=" * 80)
    print("FLOOR-WISE DATA DIAGNOSTIC TOOL")
    print("=" * 80)
    print()
    
    try:
        conn = sqlite3.connect('construction.db')
        c = conn.cursor()
        
        # 1. Check if sites table has floor columns
        print("1️⃣  Checking Sites Table Schema...")
        c.execute("PRAGMA table_info(sites)")
        columns = c.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"   Columns in sites table: {len(columns)}")
        for col in columns:
            print(f"      - {col[1]} ({col[2]})")
        
        has_floor_columns = all(col in column_names for col in ['num_basements', 'num_floors', 'has_roof'])
        
        if has_floor_columns:
            print("   ✅ Floor columns exist in sites table")
        else:
            print("   ❌ MISSING FLOOR COLUMNS IN SITES TABLE!")
            print("   🔧 Fix: Run 'python migrate_database.py'")
            print()
        
        # 2. Check sites configuration
        print("\n2️⃣  Checking Sites Configuration...")
        if has_floor_columns:
            c.execute("SELECT id, name, num_basements, num_floors, has_roof FROM sites")
        else:
            c.execute("SELECT id, name FROM sites")
        
        sites = c.fetchall()
        
        if sites:
            print(f"   Total sites: {len(sites)}")
            for site in sites:
                if has_floor_columns:
                    site_id, name, basements, floors, roof = site
                    print(f"   📍 [{site_id}] {name}")
                    print(f"      - Basements: {basements}")
                    print(f"      - Floors: {floors}")
                    print(f"      - Has Roof: {'Yes' if roof else 'No'}")
                else:
                    site_id, name = site
                    print(f"   📍 [{site_id}] {name} (No floor config)")
        else:
            print("   ⚠️  No sites found in database")
        
        # 3. Check progress entries
        print("\n3️⃣  Checking Progress Entries...")
        c.execute("SELECT COUNT(*) FROM progress")
        total_progress = c.fetchone()[0]
        print(f"   Total progress entries: {total_progress}")
        
        if total_progress > 0:
            # Check for floor-wise details
            c.execute("SELECT id, description FROM progress")
            all_progress = c.fetchall()
            
            floor_data_count = 0
            sample_floor_data = []
            
            for prog_id, description in all_progress:
                if "--- FLOOR-WISE DETAILS ---" in description:
                    floor_data_count += 1
                    if len(sample_floor_data) < 3:
                        # Extract floor info
                        parts = description.split("--- FLOOR-WISE DETAILS ---")
                        if len(parts) > 1:
                            floor_section = parts[1][:200]  # First 200 chars
                            sample_floor_data.append((prog_id, floor_section))
            
            print(f"   Entries with floor-wise data: {floor_data_count} / {total_progress}")
            
            if floor_data_count > 0:
                print("   ✅ Floor-wise data found!")
                print("\n   📋 Sample floor-wise entries:")
                for prog_id, floor_section in sample_floor_data:
                    print(f"\n   Progress ID {prog_id}:")
                    for line in floor_section.split('\n')[:5]:
                        if line.strip():
                            print(f"      {line.strip()}")
            else:
                print("   ❌ NO FLOOR-WISE DATA FOUND!")
                print("   🔧 Fix: Upload new progress using the updated form with floor selection")
                print("         The form should have 'Floor-wise Progress Details' section")
        
        # 4. Test floor-wise parsing function
        print("\n4️⃣  Testing Floor-wise Parsing Function...")
        if total_progress > 0 and sites:
            from database import get_floor_wise_progress, get_work_type_breakdown
            
            test_site_id = sites[0][0]
            print(f"   Testing with Site ID: {test_site_id}")
            
            floor_data = get_floor_wise_progress(test_site_id)
            work_data = get_work_type_breakdown(test_site_id)
            
            if floor_data:
                print(f"   ✅ Floor data parsed successfully: {len(floor_data)} floors")
                for floor_row in floor_data:
                    floor, updates, avg_prog, phase, work_count = floor_row
                    print(f"      - {floor}: {updates} updates, {avg_prog:.1f}% avg progress")
            else:
                print("   ⚠️  No floor data returned from parsing")
            
            if work_data:
                print(f"   ✅ Work type data parsed successfully: {len(work_data)} work types")
                for work_row in work_data[:3]:
                    work_name, total, completed, in_prog = work_row
                    print(f"      - {work_name}: {completed}/{total} completed")
            else:
                print("   ⚠️  No work type data returned from parsing")
        
        # 5. Summary and recommendations
        print("\n" + "=" * 80)
        print("DIAGNOSIS SUMMARY")
        print("=" * 80)
        
        issues = []
        fixes = []
        
        if not has_floor_columns:
            issues.append("❌ Sites table missing floor columns")
            fixes.append("Run: python migrate_database.py")
        
        if total_progress == 0:
            issues.append("⚠️  No progress data in database")
            fixes.append("Upload some progress updates through the app")
        elif floor_data_count == 0:
            issues.append("❌ No progress entries with floor-wise data")
            fixes.append("Upload new progress using the updated form (should have floor selection)")
        
        if issues:
            print("\n🔍 Issues Found:")
            for issue in issues:
                print(f"   {issue}")
            
            print("\n🔧 Recommended Fixes:")
            for i, fix in enumerate(fixes, 1):
                print(f"   {i}. {fix}")
        else:
            print("\n✅ All checks passed! Floor-wise data should be visible in the app.")
            print("\n💡 If you still don't see metrics:")
            print("   1. Restart the Streamlit app")
            print("   2. Clear browser cache")
            print("   3. Check the 'Analytics & Visualizations' tab")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"\n❌ Database Error: {e}")
        print("\n🔧 Fix: Make sure 'construction.db' exists")
        print("   Run: python app/database.py")
        return
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\n🔧 Fix: Make sure you're in the correct directory")
        return
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    diagnose_floor_data()

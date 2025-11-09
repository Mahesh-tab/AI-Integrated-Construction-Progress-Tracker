"""
Verification script to check if work status details are being saved correctly
"""
import sqlite3
import sys

def verify_work_status():
    print("=" * 80)
    print("WORK STATUS VERIFICATION")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect('construction.db')
        c = conn.cursor()
        
        # Get all progress entries
        c.execute("SELECT id, site_id, date, description FROM progress ORDER BY id DESC LIMIT 5")
        entries = c.fetchall()
        
        if not entries:
            print("\n❌ No progress entries found in database")
            print("   Please upload a progress update first")
            conn.close()
            return
        
        print(f"\n📊 Found {len(entries)} recent progress entries\n")
        
        for entry_id, site_id, date, description in entries:
            print(f"{'=' * 80}")
            print(f"Entry ID: {entry_id} | Date: {date}")
            print(f"{'=' * 80}")
            
            # Check for floor-wise details marker
            if "--- FLOOR-WISE DETAILS ---" in description:
                print("✅ Contains floor-wise details")
                
                # Extract floor section
                parts = description.split("--- FLOOR-WISE DETAILS ---")
                if len(parts) > 1:
                    floor_section = parts[1]
                    
                    # Extract floor info
                    for line in floor_section.split('\n')[:10]:
                        if line.strip() and not line.strip().startswith('Work Types'):
                            print(f"   {line}")
                    
                    # Check for work types
                    if "Work Types Being Carried Out:" in description:
                        print("\n✅ Contains work types:")
                        
                        work_parts = description.split("Work Types Being Carried Out:")
                        if len(work_parts) > 1:
                            work_section = work_parts[1]
                            work_lines = [line.strip() for line in work_section.split('\n') 
                                        if line.strip().startswith('-')]
                            
                            if work_lines:
                                for line in work_lines:
                                    # Parse work name and status
                                    if ':' in line:
                                        work_name = line.split(':')[0].replace('-', '').strip()
                                        status = line.split(':')[1].strip() if len(line.split(':')) > 1 else "Unknown"
                                        
                                        # Determine status category
                                        if 'Completed' in status:
                                            status_emoji = "✅"
                                        elif 'progress' in status.lower() or '%' in status:
                                            status_emoji = "🔄"
                                        elif 'Started' in status:
                                            status_emoji = "🟡"
                                        elif 'Pending' in status:
                                            status_emoji = "⏸️"
                                        else:
                                            status_emoji = "❓"
                                        
                                        print(f"      {status_emoji} {work_name}: {status}")
                            else:
                                print("      ⚠️ No work lines found (lines don't start with '-')")
                                print(f"      Raw work section: {work_section[:200]}")
                    else:
                        print("\n❌ No 'Work Types Being Carried Out:' section found")
                else:
                    print("   ⚠️ Floor section is empty")
            else:
                print("❌ No floor-wise details found")
                print("   This is an old entry created before floor-wise feature")
            
            print()
        
        # Test the database function
        print("=" * 80)
        print("TESTING DATABASE PARSING FUNCTIONS")
        print("=" * 80)
        
        from app.database import get_work_type_breakdown, get_floor_wise_progress
        
        # Get unique site IDs
        c.execute("SELECT DISTINCT site_id FROM progress")
        site_ids = [row[0] for row in c.fetchall()]
        
        for site_id in site_ids:
            print(f"\nSite ID: {site_id}")
            
            # Test work type breakdown
            work_data = get_work_type_breakdown(site_id)
            if work_data:
                print(f"  ✅ Work Type Breakdown: {len(work_data)} work types found")
                for work_name, total, completed, in_progress in work_data:
                    completion_rate = (completed / total * 100) if total > 0 else 0
                    print(f"     - {work_name}: {completed}/{total} completed ({completion_rate:.0f}%)")
            else:
                print("  ❌ No work type data parsed")
            
            # Test floor-wise progress
            floor_data = get_floor_wise_progress(site_id)
            if floor_data:
                print(f"  ✅ Floor-wise Progress: {len(floor_data)} floors found")
                for floor, updates, avg_prog, phase, work_count in floor_data:
                    print(f"     - {floor}: {updates} updates, {avg_prog:.1f}% avg progress, {work_count} work types")
            else:
                print("  ❌ No floor-wise data parsed")
        
        conn.close()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("\n✅ Fixed Issues:")
        print("   - Removed duplicate work_status_details initialization")
        print("   - work_status_details now properly initialized outside if block")
        print("\n📋 Next Steps:")
        print("   1. Upload a NEW progress entry using the updated form")
        print("   2. Make sure to check at least one work type checkbox")
        print("   3. Set the status for each checked work type")
        print("   4. Upload photos and submit")
        print("   5. Go to Analytics tab to see floor-wise and work type charts")
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_work_status()

"""
Migration script to add floor configuration columns to existing sites
Run this once to update the database schema for existing sites
"""
import sqlite3

def migrate_database():
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    
    print("Checking database schema...")
    
    # Check if the new columns exist
    c.execute("PRAGMA table_info(sites)")
    columns = [col[1] for col in c.fetchall()]
    
    changes_made = False
    
    if 'num_basements' not in columns:
        print("Adding num_basements column...")
        c.execute("ALTER TABLE sites ADD COLUMN num_basements INTEGER DEFAULT 0")
        changes_made = True
    else:
        print("✓ num_basements column already exists")
    
    if 'num_floors' not in columns:
        print("Adding num_floors column...")
        c.execute("ALTER TABLE sites ADD COLUMN num_floors INTEGER DEFAULT 10")
        changes_made = True
    else:
        print("✓ num_floors column already exists")
    
    if 'has_roof' not in columns:
        print("Adding has_roof column...")
        c.execute("ALTER TABLE sites ADD COLUMN has_roof INTEGER DEFAULT 1")
        changes_made = True
    else:
        print("✓ has_roof column already exists")
    
    if changes_made:
        conn.commit()
        
        # Update existing sites with default values if they're NULL
        c.execute("""UPDATE sites 
                     SET num_basements = COALESCE(num_basements, 0),
                         num_floors = COALESCE(num_floors, 10),
                         has_roof = COALESCE(has_roof, 1)
                     WHERE num_basements IS NULL OR num_floors IS NULL OR has_roof IS NULL""")
        conn.commit()
        print("\n✅ Migration completed successfully!")
    else:
        print("\n✅ Database already up to date!")
    
    print("\nCurrent sites configuration:")
    c.execute("SELECT id, name, num_basements, num_floors, has_roof FROM sites")
    sites = c.fetchall()
    
    if sites:
        for site in sites:
            site_id, name, basements, floors, roof = site
            print(f"  [{site_id}] {name}:")
            print(f"      → {basements} basement(s), ground floor, {floors} floor(s)" + 
                  (", roof/terrace" if roof else ""))
    else:
        print("  No sites found in database.")
    
    conn.close()

if __name__ == '__main__':
    migrate_database()

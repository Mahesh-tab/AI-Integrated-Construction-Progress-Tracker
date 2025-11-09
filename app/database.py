import sqlite3
import bcrypt

def init_db():
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()

    # User table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Sites table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            status TEXT DEFAULT 'Active',
            num_basements INTEGER DEFAULT 0,
            num_floors INTEGER DEFAULT 10,
            has_roof INTEGER DEFAULT 1
        )
    ''')

    # Progress table
    c.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            image BLOB NOT NULL,
            ai_report TEXT NOT NULL,
            ai_verification_status TEXT NOT NULL,
            progress_percentage INTEGER DEFAULT 0,
            FOREIGN KEY (site_id) REFERENCES sites (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

def add_user(username, password, role):
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True

def get_user(username):
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users")
    users = c.fetchall()
    conn.close()
    return users

def add_site(name, location, description='', start_date='', num_basements=0, num_floors=10, has_roof=True):
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO sites (name, location, description, start_date, status, num_basements, num_floors, has_roof) 
                     VALUES (?, ?, ?, ?, 'Active', ?, ?, ?)""", 
                  (name, location, description, start_date, num_basements, num_floors, 1 if has_roof else 0))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True

def get_sites():
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sites ORDER BY id DESC")
    sites = c.fetchall()
    conn.close()
    return sites

def get_site_by_id(site_id):
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
    site = c.fetchone()
    conn.close()
    return site

def update_site_status(site_id, status):
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("UPDATE sites SET status = ? WHERE id = ?", (status, site_id))
    conn.commit()
    conn.close()

def add_progress(site_id, user_id, date, category, description, image, ai_report, ai_verification_status, progress_percentage=0):
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("""INSERT INTO progress (site_id, user_id, date, category, description, image, ai_report, 
                 ai_verification_status, progress_percentage) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (site_id, user_id, date, category, description, image, ai_report, ai_verification_status, progress_percentage))
    conn.commit()
    conn.close()

def get_progress_by_site(site_id):
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("""SELECT p.id, p.date, u.username, p.category, p.description, p.image, p.ai_report, 
                 p.ai_verification_status, p.progress_percentage 
                 FROM progress p 
                 JOIN users u ON p.user_id = u.id 
                 WHERE p.site_id = ? 
                 ORDER BY p.date DESC""", (site_id,))
    progress = c.fetchall()
    conn.close()
    return progress

def get_site_statistics(site_id):
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    
    # Total updates
    c.execute("SELECT COUNT(*) FROM progress WHERE site_id = ?", (site_id,))
    total_updates = c.fetchone()[0]
    
    # Latest progress percentage
    c.execute("SELECT progress_percentage FROM progress WHERE site_id = ? ORDER BY date DESC LIMIT 1", (site_id,))
    result = c.fetchone()
    latest_progress = result[0] if result else 0
    
    # Verification stats
    c.execute("SELECT ai_verification_status, COUNT(*) FROM progress WHERE site_id = ? GROUP BY ai_verification_status", (site_id,))
    verification_stats = dict(c.fetchall())
    
    conn.close()
    return {
        'total_updates': total_updates,
        'latest_progress': latest_progress,
        'verification_stats': verification_stats
    }

def get_all_statistics():
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    
    # Total sites
    c.execute("SELECT COUNT(*) FROM sites")
    total_sites = c.fetchone()[0]
    
    # Total updates
    c.execute("SELECT COUNT(*) FROM progress")
    total_updates = c.fetchone()[0]
    
    # Active sites
    c.execute("SELECT COUNT(*) FROM sites WHERE status = 'Active'")
    active_sites = c.fetchone()[0]
    
    conn.close()
    return {
        'total_sites': total_sites,
        'total_updates': total_updates,
        'active_sites': active_sites
    }

def get_progress_timeline(site_id):
    """Get progress percentage over time for timeline chart"""
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("""SELECT date, progress_percentage, category 
                 FROM progress 
                 WHERE site_id = ? 
                 ORDER BY date ASC""", (site_id,))
    timeline = c.fetchall()
    conn.close()
    return timeline

def get_category_breakdown(site_id):
    """Get count of updates by category"""
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("""SELECT category, COUNT(*) as count 
                 FROM progress 
                 WHERE site_id = ? 
                 GROUP BY category""", (site_id,))
    breakdown = c.fetchall()
    conn.close()
    return breakdown

def get_verification_breakdown(site_id):
    """Get count of updates by verification status"""
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("""SELECT ai_verification_status, COUNT(*) as count 
                 FROM progress 
                 WHERE site_id = ? 
                 GROUP BY ai_verification_status""", (site_id,))
    breakdown = c.fetchall()
    conn.close()
    return breakdown

def get_monthly_progress(site_id):
    """Get progress updates grouped by month"""
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("""SELECT strftime('%Y-%m', date) as month, COUNT(*) as count,
                 AVG(progress_percentage) as avg_progress
                 FROM progress 
                 WHERE site_id = ? 
                 GROUP BY month
                 ORDER BY month ASC""", (site_id,))
    monthly = c.fetchall()
    conn.close()
    return monthly

def get_floor_wise_progress(site_id):
    """Get progress updates grouped by floor"""
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("""SELECT description FROM progress WHERE site_id = ?""", (site_id,))
    results = c.fetchall()
    conn.close()
    
    # Parse floor information from descriptions
    floor_stats = {}
    for (description,) in results:
        if "--- FLOOR-WISE DETAILS ---" in description:
            parts = description.split("--- FLOOR-WISE DETAILS ---")
            if len(parts) > 1:
                floor_section = parts[1]
                
                # Extract floor
                floor_name = "Unknown"
                if "Floor: " in floor_section:
                    floor_line = [line for line in floor_section.split('\n') if "Floor: " in line]
                    if floor_line:
                        floor_name = floor_line[0].replace("Floor: ", "").strip()
                
                # Extract floor progress
                floor_progress = 0
                if "Floor Progress: " in floor_section:
                    prog_line = [line for line in floor_section.split('\n') if "Floor Progress: " in line]
                    if prog_line:
                        prog_str = prog_line[0].replace("Floor Progress: ", "").strip().replace("%", "")
                        try:
                            floor_progress = int(prog_str)
                        except:
                            floor_progress = 0
                
                # Extract work phase
                work_phase = "Unknown"
                if "Work Phase: " in floor_section:
                    phase_line = [line for line in floor_section.split('\n') if "Work Phase: " in line]
                    if phase_line:
                        work_phase = phase_line[0].replace("Work Phase: ", "").strip()
                
                # Aggregate stats
                if floor_name not in floor_stats:
                    floor_stats[floor_name] = {
                        'count': 0,
                        'total_progress': 0,
                        'phases': [],
                        'work_types': []
                    }
                
                floor_stats[floor_name]['count'] += 1
                floor_stats[floor_name]['total_progress'] += floor_progress
                floor_stats[floor_name]['phases'].append(work_phase)
                
                # Extract work types
                if "Work Types Being Carried Out:" in floor_section:
                    work_section = floor_section.split("Work Types Being Carried Out:")[1]
                    work_lines = [line.strip() for line in work_section.split('\n') if line.strip().startswith('-')]
                    for line in work_lines:
                        work_name = line.split(':')[0].replace('-', '').strip()
                        if work_name not in floor_stats[floor_name]['work_types']:
                            floor_stats[floor_name]['work_types'].append(work_name)
    
    # Calculate averages and format
    result = []
    for floor, stats in floor_stats.items():
        avg_progress = stats['total_progress'] / stats['count'] if stats['count'] > 0 else 0
        latest_phase = stats['phases'][-1] if stats['phases'] else "Unknown"
        work_types_count = len(stats['work_types'])
        result.append((floor, stats['count'], avg_progress, latest_phase, work_types_count))
    
    return result

def get_work_type_breakdown(site_id):
    """Get breakdown of work types across all floors"""
    conn = sqlite3.connect('construction.db')
    c = conn.cursor()
    c.execute("""SELECT description FROM progress WHERE site_id = ?""", (site_id,))
    results = c.fetchall()
    conn.close()
    
    work_type_stats = {}
    
    for (description,) in results:
        if "Work Types Being Carried Out:" in description:
            parts = description.split("Work Types Being Carried Out:")
            if len(parts) > 1:
                work_section = parts[1].split("---")[0] if "---" in parts[1] else parts[1]
                work_lines = [line.strip() for line in work_section.split('\n') if line.strip().startswith('-')]
                
                for line in work_lines:
                    work_name = line.split(':')[0].replace('-', '').strip()
                    status = line.split(':')[1].strip() if ':' in line else "Unknown"
                    
                    if work_name not in work_type_stats:
                        work_type_stats[work_name] = {
                            'total': 0,
                            'completed': 0,
                            'in_progress': 0,
                            'started': 0
                        }
                    
                    work_type_stats[work_name]['total'] += 1
                    if 'Completed' in status:
                        work_type_stats[work_name]['completed'] += 1
                    elif 'progress' in status.lower():
                        work_type_stats[work_name]['in_progress'] += 1
                    elif 'Started' in status:
                        work_type_stats[work_name]['started'] += 1
    
    return [(name, stats['total'], stats['completed'], stats['in_progress']) 
            for name, stats in work_type_stats.items()]

if __name__ == '__main__':
    init_db()
    # Add a default admin user if not exists
    if not get_user('admin'):
        add_user('admin', 'admin', 'admin')
    if not get_user('engineer'):
        add_user('engineer', 'engineer', 'engineer')

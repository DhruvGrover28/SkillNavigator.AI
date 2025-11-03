import sqlite3

def check_database():
    conn = sqlite3.connect('backend/skillnavigator.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tables:', [t[0] for t in tables])
    
    # Check jobs count
    try:
        cursor.execute('SELECT COUNT(*) FROM jobs')
        jobs_count = cursor.fetchone()[0]
        print('Jobs count:', jobs_count)
        
        # Check sample job
        cursor.execute('SELECT title, company, location FROM jobs LIMIT 3')
        sample_jobs = cursor.fetchall()
        print('Sample jobs:', sample_jobs)
    except Exception as e:
        print('Jobs table error:', e)
    
    # Check users count
    try:
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        print('Users count:', users_count)
        
        if users_count > 0:
            cursor.execute('SELECT id, email, name FROM users LIMIT 3')
            sample_users = cursor.fetchall()
            print('Sample users:', sample_users)
    except Exception as e:
        print('Users table error:', e)
    
    # Check applications count
    try:
        cursor.execute('SELECT COUNT(*) FROM job_applications')
        apps_count = cursor.fetchone()[0]
        print('Applications count:', apps_count)
        
        if apps_count > 0:
            cursor.execute('SELECT id, job_id, status FROM job_applications LIMIT 3')
            sample_apps = cursor.fetchall()
            print('Sample applications:', sample_apps)
    except Exception as e:
        print('Applications table error:', e)
    
    conn.close()

if __name__ == "__main__":
    check_database()
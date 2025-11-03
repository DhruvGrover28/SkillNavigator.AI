import sqlite3

def check_job_sources():
    conn = sqlite3.connect('backend/skillnavigator.db')
    cursor = conn.cursor()
    
    # Check job sources
    cursor.execute('SELECT DISTINCT source FROM jobs ORDER BY source')
    sources = cursor.fetchall()
    print('Job sources:', [s[0] for s in sources])
    
    # Check some real job data
    cursor.execute('SELECT title, company, location, source, description FROM jobs LIMIT 5')
    sample_jobs = cursor.fetchall()
    print('\nSample job data:')
    for job in sample_jobs:
        print(f"Title: {job[0]}")
        print(f"Company: {job[1]}")
        print(f"Location: {job[2]}")
        print(f"Source: {job[3]}")
        print(f"Description: {job[4][:100]}...")
        print("---")
    
    # Check when jobs were added
    cursor.execute('SELECT created_at FROM jobs LIMIT 5')
    dates = cursor.fetchall()
    print('Sample creation dates:', dates)
    
    conn.close()

if __name__ == "__main__":
    check_job_sources()
import sqlite3

def analyze_job_data():
    conn = sqlite3.connect('backend/skillnavigator.db')
    cursor = conn.cursor()
    
    # Check job count by source
    cursor.execute('SELECT source, COUNT(*) FROM jobs GROUP BY source ORDER BY COUNT(*) DESC')
    source_counts = cursor.fetchall()
    print('Jobs by source:')
    for source, count in source_counts:
        print(f"  {source}: {count} jobs")
    
    # Check if descriptions are templated
    cursor.execute('SELECT description FROM jobs LIMIT 10')
    descriptions = cursor.fetchall()
    print('\nFirst few descriptions:')
    for i, desc in enumerate(descriptions):
        print(f"{i+1}. {desc[0][:150]}...")
    
    # Check URL patterns
    cursor.execute('SELECT DISTINCT url FROM jobs WHERE url IS NOT NULL LIMIT 10')
    urls = cursor.fetchall()
    print('\nSample URLs:')
    for url in urls:
        print(f"  {url[0]}")
    
    # Check skills data
    cursor.execute('SELECT skills FROM jobs WHERE skills IS NOT NULL LIMIT 5')
    skills = cursor.fetchall()
    print('\nSample skills:')
    for skill in skills:
        print(f"  {skill[0]}")
    
    conn.close()

if __name__ == "__main__":
    analyze_job_data()
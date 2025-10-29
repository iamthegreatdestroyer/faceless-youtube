#!/usr/bin/env python
"""Fix database user password"""

import psycopg2

try:
    # Connect as postgres admin
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='postgres',
        user='postgres',
        password='FacelessYT2025!'
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # Update the password
    cursor.execute("ALTER USER faceless_youtube WITH PASSWORD 'FacelessYT2025!';")
    print('✓ Password updated for faceless_youtube user')
    
    # Grant privileges on schema public
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO faceless_youtube;")
    cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO faceless_youtube;")
    print('✓ Privileges granted')

    conn.close()
    print('✓ Done!')
    
except Exception as e:
    print(f'✗ Error: {e}')

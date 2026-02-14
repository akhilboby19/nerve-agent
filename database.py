import sqlite3

# We use a file-based SQLite db. 
# "check_same_thread=False" is needed because FastAPI runs in multiple threads.
DB_NAME = "nerve.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the time-series schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We create a table optimized for time-series queries.
    # We index 'hostname' and 'timestamp' because that's how we will query data for dashboards.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            hostname TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            boot_time DATETIME,
            cpu_percent REAL,
            ram_percent REAL,
            disk_percent REAL,
            net_sent_mb REAL,
            net_recv_mb REAL
        )
    ''')
    
    # Indices are crucial for performance as the dataset grows
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_host_time ON system_metrics (hostname, timestamp)')
    
    conn.commit()
    conn.close()
    print("--- Database Initialized ---")

# Helper to save a metric
def save_metric(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO system_metrics (
            agent_id, hostname, timestamp, boot_time, 
            cpu_percent, ram_percent, disk_percent, net_sent_mb, net_recv_mb
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['agent_id'],
        data['hostname'],
        data['timestamp'],
        data.get('boot_time'), # .get() allows it to be nullable if missing
        data['cpu'],
        data['ram'],
        data['disk'],
        data['net_sent_mb'],
        data['net_recv_mb']
    ))
    
    conn.commit()
    conn.close()
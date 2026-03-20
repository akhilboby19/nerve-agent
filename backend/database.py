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

def get_all_agents():
    """
    Returns all known agents with their hostname, last seen timestamp,
    and online status. An agent is considered online if its last metric
    arrived within the last 10 seconds.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute('''
        SELECT
            agent_id,
            hostname,
            MAX(timestamp) as last_seen,
            CASE
                WHEN MAX(timestamp) >= datetime('now', '-10 seconds') THEN 'online'
                ELSE 'offline'
            END as status
        FROM system_metrics
        GROUP BY agent_id
        ORDER BY last_seen DESC
    ''')
 
    rows = cursor.fetchall()
    conn.close()
 
    return [dict(row) for row in rows]
 
 
def get_latest_metric(agent_id: str):
    """
    Returns the single most recent metric row for a given agent.
    Used for the current-value cards on the dashboard.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute('''
        SELECT
            agent_id,
            hostname,
            timestamp,
            cpu_percent,
            ram_percent,
            disk_percent,
            net_sent_mb,
            net_recv_mb
        FROM system_metrics
        WHERE agent_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (agent_id,))
 
    row = cursor.fetchone()
    conn.close()
 
    return dict(row) if row else None


# Maps the range query param to a SQLite datetime modifier
RANGE_MAP = {
    "1h":  "-1 hours",
    "6h":  "-6 hours",
    "12h": "-12 hours",
}
 
# Maps the resolution query param to a SQL bucket expression
RESOLUTION_MAP = {
    "1m":  "strftime('%Y-%m-%dT%H:%M:00', timestamp)",
    "5m":  "strftime('%Y-%m-%dT%H:', timestamp) || printf('%02d', (CAST(strftime('%M', timestamp) AS INTEGER) / 5) * 5) || ':00'",
    "15m": "strftime('%Y-%m-%dT%H:', timestamp) || printf('%02d', (CAST(strftime('%M', timestamp) AS INTEGER) / 15) * 15) || ':00'",
}
 
 
def get_metrics(agent_id: str, range: str = "1h", resolution: str = "1m"):
    """
    Returns downsampled time-series metrics for a given agent.
 
    range:      how far back to look       — "1h", "6h", "12h"
    resolution: size of each time bucket   — "1m", "5m", "15m"
 
    Each row in the result is one bucket containing averaged values
    for all raw metric rows that fell within that bucket's time window.
    """
    range_modifier  = RANGE_MAP.get(range, "-1 hours")
    bucket_expr     = RESOLUTION_MAP.get(resolution, RESOLUTION_MAP["1m"])
 
    query = f'''
        SELECT
            {bucket_expr} as bucket,
            AVG(cpu_percent)  as cpu,
            AVG(ram_percent)  as ram,
            AVG(disk_percent) as disk,
            AVG(net_sent_mb)  as net_sent,
            AVG(net_recv_mb)  as net_recv
        FROM system_metrics
        WHERE agent_id = ?
        AND timestamp >= datetime('now', '{range_modifier}')
        GROUP BY {bucket_expr}
        ORDER BY bucket ASC
    '''
 
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, (agent_id,))
    rows = cursor.fetchall()
    conn.close()
 
    return [dict(row) for row in rows]
 
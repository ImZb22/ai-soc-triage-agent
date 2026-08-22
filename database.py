import sqlite3

def init_db():
    conn = sqlite3.connect("soc_data.db")
    cursor = conn.cursor()
    
    #1. Raw log tables (Mini SIEM)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS raw_logs(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                       source_ip TEXT,
                       user_id TEXT,
                       event_type TEXT,
                       severity TEXT,
                       raw_message TEXT,
                       status TEXT DEFAULT 'UNPROCESSED')""")

    #2. AI Investigation Table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS alert_history(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       log_id INTEGER,
                       ai_thought_trace TEXT,
                       decision TEXT,
                       timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY(log_id) REFERENCES raw_logs(id)
                   )
                   """)
    
    #3.Containent table (Mini SOAR)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS blocked_entities(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       entity_type TEXT,
                       entity_value TEXT UNIQUE,
                       reason TEXT,
                       blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP 
                   )
                   """)
    
    conn.commit()
    conn.close()
    print("Database and tables successfully initialized!")
if __name__ == "__main__":
    init_db()

    """ 
this sets up a permanent SQLite db file (soc_data.db) file. this will act as our central storage unit
it contains 3 specific tables, each with a different purpose.
1. Table 1: raw_logs (Mini SIEM intake)
- Stores Raw, unanalyzed security events injected into the database. 
- Tracks event details and processing status (UNPROCESSED vs PROCESSED).	
- e.g. 
IP: 172.16.0.88, 
Severity: HIGH, 
Event: SQL_INJECTION_ATTEMPT, 
Status: UNPROCESSED

2. Table 2: alert_history (AI Reasoning Notebook)	
- Step-by-step ReAct thought traces generated during analysis, linking back to the log ID and storing the final triage decision (CONTAINED or MONITORED).	
-e.g. 
Thought Trace: "Analyzing HIGH event... Executing containment...", 
Decision: CONTAINED

3. Table 3: blocked_entities (Mini SOAR Enforcement)	
- Active blocklist reserved strictly for high-risk threats (CRITICAL/HIGH) that require automated isolation.
- Routine logs are never added here.	
- e.g. 
Entity Type: IP, 
Entity Value: 172.16.0.88, 
Reason: Automated block due to SQL_INJECTION_ATTEMPT

    """

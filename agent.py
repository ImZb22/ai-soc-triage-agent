import sqlite3
import time

def get_unprocessed_logs():
    conn = sqlite3.connect("soc_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, source_ip, user_id, event_type, severity, raw_message FROM raw_logs WHERE status = 'UNPROCESSED'")
    logs = cursor.fetchall()
    conn.close()
    return logs

def contain_entity(entity_type, entity_value, reason):
    conn = sqlite3.connect("soc_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO blocked_entities (entity_type, entity_value, reason)
            VALUES (?, ?, ?)
        """, (entity_type, entity_value, reason))
        conn.commit()
        print(f"  [SOAR ACTION] Blocked {entity_type}: {entity_value}")
    except sqlite3.IntegrityError:
        print(f"  [SOAR ACTION] {entity_type} {entity_value} is already in blocklist.")
    conn.close()

def update_log_status(log_id, thought_trace, decision):
    conn = sqlite3.connect("soc_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE raw_logs SET status = 'PROCESSED' WHERE id = ?", (log_id,))
    cursor.execute("""
        INSERT INTO alert_history (log_id, ai_thought_trace, decision)
        VALUES (?, ?, ?)
    """, (log_id, thought_trace, decision))
    conn.commit()
    conn.close()

def run_agent_loop():
    logs = get_unprocessed_logs()
    if not logs:
        print("No new unprocessed logs found in SIEM.")
        return

    print(f"\nFound {len(logs)} unprocessed log(s). Starting AI Triage Loop...\n" + "="*50)

    for log in logs:
        log_id, source_ip, user_id, event_type, severity, raw_message = log

        # Step 1: THOUGHT
        thought = f"Analyzing {severity} event '{event_type}' from IP {source_ip}."
        print(f"[THOUGHT]: {thought}")

        # Step 2: ACTION
        if severity in ["CRITICAL", "HIGH"]:
            action_desc = f"High risk event detected ({event_type}). Executing automated containment on IP {source_ip}."
            print(f"[ACTION]: {action_desc}")
            contain_entity("IP", source_ip, f"Automated block due to {event_type}")
            decision = "CONTAINED"
        else:
            action_desc = "Low/Medium severity event. No immediate containment needed."
            print(f"[ACTION]: {action_desc}")
            decision = "MONITORED"

        # Step 3: OBSERVATION
        observation = f"Log ID {log_id} successfully triaged with outcome: {decision}."
        print(f"[OBSERVATION]: {observation}\n" + "-"*50)

        # Save AI trace to SQLite database
        full_trace = f"THOUGHT: {thought} | ACTION: {action_desc} | OBSERVATION: {observation}"
        update_log_status(log_id, full_trace, decision)

if __name__ == "__main__":
    run_agent_loop()
# mock event simulator as we do not have live enterprise network running to collect telemetry(logs,firewalls, servers..)
# ------------------------------------------------------------------------

import sqlite3
import random
import time

#---------Mini SIEM---------
SAMPLE_EVENTS = [
    {
        "source_ip": "192.168.1.105",
        "user_id": "admin_user",
        "event_type": "SSH_BRUTE_FORCE",
        "severity": "CRITICAL",
        "raw_message": "Multiple failed SSH login attempts detected within 10 seconds."
    },
    {
        "source_ip": "10.0.0.42",
        "user_id": "john_doe",
        "event_type": "FAILED_LOGIN",
        "severity": "LOW",
        "raw_message": "User entered wrong password once."
    },
    {
        "source_ip": "172.16.0.88",
        "user_id": "guest_account",
        "event_type": "SQL_INJECTION_ATTEMPT",
        "severity": "HIGH",
        "raw_message": "Payload detected: SELECT * FRO users WHERE '1'='1'"
    },
    {
        "source_ip": "127.0.0.1",
        "user_id": "system_service",
        "event_type": "SYSTEM_CHECK",
        "severity": "INFO",
        "raw_message": "Routine internal health check completed."
    }
]
def generate_log():
    conn = sqlite3.connect("soc_data.db")  #conn is the teleph. that cncts us to db
    cursor = conn.cursor()  #--------------cursor is the voice speaking th cmds. i.e.e helps us exe SQL cmds 
            
    #picking random event from our list
    event = random.choice(SAMPLE_EVENTS)
        
    cursor.execute("""
                   INSERT INTO raw_logs(source_ip, user_id, event_type, severity, raw_message)
                   VALUES (?,?,?,?,?)
                   """,
                   (event['source_ip'], event['user_id'], event['event_type'], event['severity'], event['raw_message']))
    conn.commit()
    conn.close()
    print(f"Logged Event:[{event['severity']}] {event['event_type']} from {event['source_ip']} ")
    
if __name__ == "__main__":
    for _ in range(3): #inserting 3 saple logs to start
        generate_log()
        time.sleep(1)
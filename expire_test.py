import sqlite3
import os

def backdate_newest_member():
    # Correctly point to the database folder
    db_path = os.path.join("database", "gym.db")
    
    # Connect to your actual local database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find the most recently added member and force their expiry date to yesterday!
    query = """
        UPDATE members 
        SET expiry_date = date('now', '-1 day') 
        WHERE id = (SELECT MAX(id) FROM members)
    """
    
    try:
        cursor.execute(query)
        conn.commit()
        print("✅ Success! The newest member's plan has been officially expired.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    backdate_newest_member()
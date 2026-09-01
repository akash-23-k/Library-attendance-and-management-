import sqlite3
from typing import Optional, Dict, Any
from core.database import get_connection, hash_password, verify_password

def authenticate_admin(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate an admin user. Returns admin dictionary if successful, None otherwise.
    """
    username = username.strip()
    if not username or not password:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT admin_id, username, password_hash, status FROM admins WHERE username = ?", (username,))
    admin = cursor.fetchone()

    if not admin:
        cursor.execute("""
            INSERT INTO audit_logs (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
        """, ("LOGIN_FAILED", "admin", username, "Non-existent username attempt"))
        conn.commit()
        conn.close()
        return None

    if admin["status"] != "ACTIVE":
        cursor.execute("""
            INSERT INTO audit_logs (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
        """, ("LOGIN_FAILED", "admin", username, "Account is inactive"))
        conn.commit()
        conn.close()
        return None

    is_valid = verify_password(password, admin["password_hash"])
    if is_valid:
        cursor.execute("""
            INSERT INTO audit_logs (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
        """, ("LOGIN_SUCCESS", "admin", username, "Successful login"))
        conn.commit()
        conn.close()
        return {
            "admin_id": admin["admin_id"],
            "username": admin["username"],
            "status": admin["status"]
        }
    else:
        cursor.execute("""
            INSERT INTO audit_logs (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
        """, ("LOGIN_FAILED", "admin", username, "Invalid password"))
        conn.commit()
        conn.close()
        return None

def change_admin_password(username: str, current_password: str, new_password: str) -> bool:
    """Change admin password after verifying current credentials."""
    username = username.strip()
    if not new_password or len(new_password) < 4:
        raise ValueError("New password must be at least 4 characters long.")

    admin = authenticate_admin(username, current_password)
    if not admin:
        raise ValueError("Current password is incorrect.")

    new_hash = hash_password(new_password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE admins SET password_hash = ? WHERE username = ?", (new_hash, username))
    cursor.execute("""
        INSERT INTO audit_logs (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
    """, ("PASSWORD_CHANGED", "admin", username, "Password updated successfully"))
    conn.commit()
    conn.close()
    return True

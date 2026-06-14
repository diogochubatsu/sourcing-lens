"""Users router — authentication and user management."""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException
import bcrypt
import jwt

router = APIRouter(prefix="/api", tags=["users"])


@router.post("/users")
def create_user(username: str = Query(..., min_length=3, max_length=50), email: str = Query(..., pattern=r'^[^@]+@[^@]+\.[^@]+$'), password: str = Query(..., min_length=8)):
    """Create a new user account."""
    from database import execute_returning as db_execute_returning

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        r = db_execute_returning(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (username, email, pw_hash)
        )
        return {"ok": True, "user_id": r[0]['id']}
    except Exception as e:
        if "duplicate" in str(e).lower():
            return {"ok": False, "error": "Username or email already exists"}
        return {"ok": False, "error": str(e)}


@router.post("/users/login")
def login(username: str = Query(..., min_length=1), password: str = Query(..., min_length=1)):
    """Authenticate user and return JWT token."""
    from database import query as db_query

    r = db_query("SELECT id, username, password_hash FROM users WHERE username=%s", (username,))
    if not r:
        return {"ok": False, "error": "Invalid credentials"}
    user = r[0]
    if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        return {"ok": False, "error": "Invalid credentials"}
    
    jwt_secret = os.environ.get('JWT_SECRET_KEY', 'change-me-in-production')
    jwt_algo = os.environ.get('JWT_ALGORITHM', 'HS256')
    jwt_hours = int(os.environ.get('JWT_EXPIRATION_HOURS', '24'))
    
    token = jwt.encode(
        {'user_id': user['id'], 'username': user['username'],
         'exp': datetime.utcnow() + timedelta(hours=jwt_hours)},
        jwt_secret, algorithm=jwt_algo
    )
    return {"ok": True, "user": {"id": user['id'], "username": user['username']}, "token": token}


@router.put("/users/{user_id}/preferences")
def update_prefs(user_id: int, preferences: dict):
    """Update user preferences."""
    from database import execute as db_execute
    import json

    db_execute("UPDATE users SET preferred_categories = %s WHERE id=%s",
            (json.dumps(preferences.get('categories', [])), user_id))
    return {"ok": True}

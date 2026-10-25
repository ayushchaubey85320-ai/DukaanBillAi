"""
JWT Authentication, Password Hashing & Role-Based Access Control
Handles Shopkeeper and Super Admin authentication without hardcoded secrets.
"""
import os
import time
import hashlib
import secrets
import jwt
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dukaan-secure-jwt-secret-key-prod-2026")
ALGORITHM = "HS256"
security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> Tuple[str, str]:
    """Hashes password with a cryptographically secure random salt using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        bytes.fromhex(salt),
        100000
    )
    return key.hex(), salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 hash and salt."""
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        bytes.fromhex(salt),
        100000
    )
    return secrets.compare_digest(key.hex(), stored_hash)

def create_access_token(data: Dict[str, Any], expires_delta_seconds: int = 86400 * 30) -> str:
    """Creates a signed JWT access token valid for 30 days."""
    to_encode = data.copy()
    expire = time.time() + expires_delta_seconds
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None

def get_current_user_from_token(token: str) -> Dict[str, Any]:
    """Validates token and returns current user payload."""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
    return payload

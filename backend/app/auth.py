"""
JWT Authentication & Shopkeeper Profile Security
"""
import time
import jwt
from typing import Dict, Any, Optional

SECRET_KEY = "indian-shopkeeper-billing-agent-secret-key-offline"
ALGORITHM = "HS256"

def create_access_token(data: Dict[str, Any], expires_delta_seconds: int = 86400 * 30) -> str:
    """Creates a JWT access token valid for 30 days."""
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

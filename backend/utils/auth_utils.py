"""
Authentication Utilities
Simple JWT and password hashing for demo purposes
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib
from jose import JWTError, jwt
import os

# Simple password hashing using hashlib (demo purposes)
def _simple_hash(password: str, salt: str = "skillnavigator-salt") -> str:
    """Simple password hashing for demo - NOT for production"""
    return hashlib.sha256((password + salt).encode()).hexdigest()

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET", "skillnavigator-demo-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days for demo


def hash_password(password: str) -> str:
    """Hash a password (demo implementation)"""
    return _simple_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return _simple_hash(plain_password) == hashed_password


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            return None
            
        return {
            "user_id": user_id,
            "email": email,
            "exp": payload.get("exp")
        }
    except JWTError:
        return None


def create_user_token(user_id: int, email: str) -> str:
    """Create a token for a specific user"""
    token_data = {
        "user_id": user_id,
        "email": email
    }
    return create_access_token(token_data)


# Demo helper functions
def is_valid_email(email: str) -> bool:
    """Simple email validation"""
    return "@" in email and "." in email.split("@")[1]


def is_strong_password(password: str) -> tuple[bool, str]:
    """Simple password validation"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if password.lower() == password:
        return False, "Password should contain at least one uppercase letter"
        
    if not any(char.isdigit() for char in password):
        return False, "Password should contain at least one number"
        
    return True, "Password is strong"


# Test function
if __name__ == "__main__":
    # Test the authentication utilities
    print("🔐 Testing Authentication Utilities...")
    
    # Test password hashing
    password = "TestPassword123"
    hashed = hash_password(password)
    print(f"✅ Password hashed: {hashed[:20]}...")
    
    # Test password verification
    is_valid = verify_password(password, hashed)
    print(f"✅ Password verification: {is_valid}")
    
    # Test JWT token creation
    token = create_user_token(1, "test@example.com")
    print(f"✅ JWT token created: {token[:30]}...")
    
    # Test token verification
    payload = verify_token(token)
    print(f"✅ Token verification: {payload}")
    
    # Test email validation
    print(f"✅ Email validation: {is_valid_email('test@example.com')}")
    
    # Test password strength
    strong, msg = is_strong_password(password)
    print(f"✅ Password strength: {strong} - {msg}")
    
    print("🎯 All authentication utilities working correctly!")
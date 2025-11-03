"""
Authentication Middleware
Extracts user information from JWT tokens for protected routes
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
from utils.auth_utils import verify_token

# Create HTTPBearer security scheme
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Extract and validate user from JWT token
    Use this as a dependency for protected routes
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token
        token = credentials.credentials
        
        # Verify and decode token
        payload = verify_token(token)
        
        if payload is None:
            raise credentials_exception
            
        return payload
        
    except Exception:
        raise credentials_exception


def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[Dict]:
    """
    Extract user from JWT token if provided (optional authentication)
    Returns None if no token or invalid token
    """
    if not credentials:
        return None
        
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return payload
    except:
        return None


# Helper function to get user ID from token
def get_user_id(current_user: Dict = Depends(get_current_user)) -> int:
    """Extract user ID from authenticated user"""
    return current_user["user_id"]


# Test function
if __name__ == "__main__":
    from utils.auth_utils import create_user_token
    
    # Create a test token
    test_token = create_user_token(1, "test@example.com")
    print(f"Test token: {test_token}")
    
    # Verify the token
    payload = verify_token(test_token)
    print(f"Token payload: {payload}")
    
    print("✅ Authentication middleware ready!")
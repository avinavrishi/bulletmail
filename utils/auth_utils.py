from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
# from jose import JWTError, jwt
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Optional
from core.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token.
    
    Args:
        data: Payload data for token
        expires_delta: Optional custom expiration time
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode.update({
        "exp": expire,
        "token_type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token.
    
    Args:
        data: Payload data for token
        expires_delta: Optional custom expiration time
    Returns:
        str: Encoded JWT token
    """
    print("Starting create_refresh_token with data:", data)
    to_encode = data.copy()
    print("Data copied successfully")
    
    try:
        expire = datetime.now(timezone.utc) + (expires_delta if expires_delta 
                                             else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        print("Expiration calculated:", expire)
        
        to_encode.update({
            "exp": expire,
            "token_type": "refresh"
        })
        print("Payload updated:", to_encode)
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        print("Token encoded successfully")
        return encoded_jwt
    except Exception as e:
        print("Error occurred:", str(e))
        raise

def verify_token(token: str, verify_type: Optional[str] = None) -> Optional[dict]:
    """Verify JWT token and optionally check token type.
    
    Args:
        token: JWT token to verify
        verify_type: Optional token type to verify ('access' or 'refresh')
    Returns:
        Optional[dict]: Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if verify_type and payload.get("token_type") != verify_type:
            return None
        return payload
    except InvalidTokenError:
        return None

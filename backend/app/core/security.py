"""
Security utilities for authentication and authorization.
"""
import secrets
import hashlib
import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import HTTPException, status

from app.core.config import settings


# Password hashing context with explicit bcrypt configuration
try:
    # Try to initialize bcrypt with safer settings
    pwd_context = CryptContext(
        schemes=["bcrypt"], 
        deprecated="auto",
        bcrypt__rounds=4  # Lower rounds for testing
    )
    # Test if bcrypt works with a simple password
    test_hash = pwd_context.hash("test")
    pwd_context.verify("test", test_hash)
except Exception as e:
    # If bcrypt fails, fall back to a simpler scheme for testing
    print(f"Bcrypt initialization failed: {e}")
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Legacy Fernet encryption for backward compatibility (AES-128)
ENCRYPTION_KEY = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'0'))
cipher_suite = Fernet(ENCRYPTION_KEY)


class PKCEChallenge:
    """PKCE (Proof Key for Code Exchange) challenge generator and verifier."""
    
    @staticmethod
    def generate_code_verifier() -> str:
        """Generate a cryptographically random code verifier."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    @staticmethod
    def generate_code_challenge(code_verifier: str) -> str:
        """Generate code challenge from verifier using SHA256."""
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    @staticmethod
    def verify_code_challenge(code_verifier: str, code_challenge: str) -> bool:
        """Verify that code verifier matches the challenge."""
        expected_challenge = PKCEChallenge.generate_code_challenge(code_verifier)
        return secrets.compare_digest(expected_challenge, code_challenge)


class TokenManager:
    """JWT token management with refresh token support."""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            # Refresh tokens last 7 days by default
            expire = datetime.utcnow() + timedelta(days=7)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check expiration (exp is already checked by jwt.decode, but let's be explicit)
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing expiration",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
    
    @staticmethod
    def create_password_reset_token(email: str) -> str:
        """Create password reset token."""
        to_encode = {
            "email": email,
            "type": "password_reset"
        }
        # Password reset tokens expire in 1 hour
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_password_reset_token(token: str) -> str:
        """Verify password reset token and return email."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            if payload.get("type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            return payload.get("email")
        except (JWTError, ExpiredSignatureError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )


class PasswordManager:
    """Password hashing and verification utilities."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        # Truncate password to 72 bytes for bcrypt compatibility
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        # Truncate password to 72 bytes for bcrypt compatibility
        if len(password.encode('utf-8')) > 72:
            password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        return pwd_context.hash(password)


class EncryptionManager:
    """Enhanced encryption utilities with AES-256 support for sensitive data."""
    
    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """Derive AES-256 key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        return kdf.derive(password.encode())
    
    @staticmethod
    def encrypt_data_aes256(data: str, password: Optional[str] = None) -> str:
        """
        Encrypt sensitive data using AES-256-GCM.
        
        Args:
            data: The data to encrypt
            password: Optional password for key derivation (uses SECRET_KEY if not provided)
            
        Returns:
            Base64 encoded encrypted data with salt and nonce
        """
        if password is None:
            password = settings.SECRET_KEY
        
        # Generate random salt and nonce
        salt = os.urandom(16)  # 128 bits
        nonce = os.urandom(12)  # 96 bits for GCM
        
        # Derive key
        key = EncryptionManager._derive_key(password, salt)
        
        # Encrypt data
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
        
        # Combine salt + nonce + tag + ciphertext
        encrypted_data = salt + nonce + encryptor.tag + ciphertext
        
        return base64.b64encode(encrypted_data).decode()
    
    @staticmethod
    def decrypt_data_aes256(encrypted_data: str, password: Optional[str] = None) -> str:
        """
        Decrypt AES-256-GCM encrypted data.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            password: Optional password for key derivation (uses SECRET_KEY if not provided)
            
        Returns:
            Decrypted data as string
        """
        if password is None:
            password = settings.SECRET_KEY
        
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # Extract components
            salt = encrypted_bytes[:16]
            nonce = encrypted_bytes[16:28]
            tag = encrypted_bytes[28:44]
            ciphertext = encrypted_bytes[44:]
            
            # Derive key
            key = EncryptionManager._derive_key(password, salt)
            
            # Decrypt data
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext.decode()
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """Legacy Fernet encryption for backward compatibility."""
        return cipher_suite.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """Legacy Fernet decryption for backward compatibility."""
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def encrypt_api_keys(api_keys: Dict[str, str], use_aes256: bool = True) -> Dict[str, str]:
        """
        Encrypt API keys dictionary using AES-256 or legacy Fernet.
        
        Args:
            api_keys: Dictionary of provider -> API key
            use_aes256: Whether to use AES-256 encryption (default: True)
            
        Returns:
            Dictionary with encrypted API keys
        """
        encrypted_keys = {}
        for provider, key in api_keys.items():
            if key:  # Only encrypt non-empty keys
                if use_aes256:
                    encrypted_keys[provider] = EncryptionManager.encrypt_data_aes256(key)
                else:
                    encrypted_keys[provider] = EncryptionManager.encrypt_data(key)
        return encrypted_keys
    
    @staticmethod
    def decrypt_api_keys(encrypted_keys: Dict[str, str], use_aes256: bool = True) -> Dict[str, str]:
        """
        Decrypt API keys dictionary.
        
        Args:
            encrypted_keys: Dictionary with encrypted API keys
            use_aes256: Whether to use AES-256 decryption (default: True)
            
        Returns:
            Dictionary with decrypted API keys
        """
        decrypted_keys = {}
        for provider, encrypted_key in encrypted_keys.items():
            if encrypted_key:  # Only decrypt non-empty keys
                try:
                    if use_aes256:
                        decrypted_keys[provider] = EncryptionManager.decrypt_data_aes256(encrypted_key)
                    else:
                        decrypted_keys[provider] = EncryptionManager.decrypt_data(encrypted_key)
                except Exception:
                    # Try the other encryption method as fallback
                    try:
                        if use_aes256:
                            decrypted_keys[provider] = EncryptionManager.decrypt_data(encrypted_key)
                        else:
                            decrypted_keys[provider] = EncryptionManager.decrypt_data_aes256(encrypted_key)
                    except Exception as e:
                        raise ValueError(f"Failed to decrypt API key for {provider}: {str(e)}")
        return decrypted_keys
    
    @staticmethod
    def secure_compare(a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        return secrets.compare_digest(a.encode(), b.encode())
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash sensitive data with salt for secure storage.
        
        Args:
            data: Data to hash
            salt: Optional salt (generates random if not provided)
            
        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        hash_bytes = kdf.derive(data.encode())
        hash_hex = hash_bytes.hex()
        
        return hash_hex, salt
    
    @staticmethod
    def verify_hashed_data(data: str, hash_hex: str, salt: str) -> bool:
        """Verify hashed data against stored hash."""
        try:
            expected_hash, _ = EncryptionManager.hash_sensitive_data(data, salt)
            return secrets.compare_digest(expected_hash, hash_hex)
        except Exception:
            return False


class RateLimiter:
    """Rate limiting utilities."""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
    
    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """Check if a key is rate limited."""
        if not self.redis_client:
            return False  # No rate limiting if Redis is not available
        
        try:
            current = await self.redis_client.get(key)
            if current is None:
                await self.redis_client.setex(key, window, 1)
                return False
            
            if int(current) >= limit:
                return True
            
            await self.redis_client.incr(key)
            return False
            
        except Exception:
            # If Redis fails, allow the request
            return False


def generate_state() -> str:
    """Generate a random state parameter for OAuth flows."""
    return secrets.token_urlsafe(32)


def verify_state(provided_state: str, expected_state: str) -> bool:
    """Verify OAuth state parameter."""
    return secrets.compare_digest(provided_state, expected_state)
"""
Data encryption service for comprehensive sensitive data protection.
Ensures all sensitive data is encrypted using AES-256-GCM.
"""
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.core.security import EncryptionManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataEncryptionService:
    """Service for encrypting and managing sensitive data across the application."""
    
    # Define which fields should be encrypted for each model
    ENCRYPTION_MAPPING = {
        "users": {
            "api_keys": "json_encrypt",  # Encrypt the entire JSON object
            "hand_history_paths": "json_encrypt_optional",  # Optional encryption for paths
        },
        "poker_hands": {
            "raw_text": "text_encrypt_optional",  # Optional encryption for hand history text
        },
        "analysis_results": {
            "analysis_text": "text_encrypt_optional",  # Optional encryption for AI analysis
            "analysis_metadata": "json_encrypt_optional",  # Optional encryption for metadata
        },
        "file_processing_tasks": {
            "error_details": "json_encrypt_optional",  # Optional encryption for error details
        }
    }
    
    @staticmethod
    def encrypt_sensitive_field(data: Any, encryption_type: str) -> Any:
        """
        Encrypt a field based on its encryption type.
        
        Args:
            data: The data to encrypt
            encryption_type: Type of encryption to apply
            
        Returns:
            Encrypted data
        """
        if data is None:
            return None
        
        try:
            if encryption_type == "json_encrypt":
                # Always encrypt JSON data
                json_str = json.dumps(data) if not isinstance(data, str) else data
                return EncryptionManager.encrypt_data_aes256(json_str)
            
            elif encryption_type == "json_encrypt_optional":
                # Encrypt JSON data if it contains sensitive information
                if DataEncryptionService._contains_sensitive_data(data):
                    json_str = json.dumps(data) if not isinstance(data, str) else data
                    return EncryptionManager.encrypt_data_aes256(json_str)
                return data
            
            elif encryption_type == "text_encrypt":
                # Always encrypt text data
                return EncryptionManager.encrypt_data_aes256(str(data))
            
            elif encryption_type == "text_encrypt_optional":
                # Encrypt text data if it's sensitive
                if DataEncryptionService._is_sensitive_text(str(data)):
                    return EncryptionManager.encrypt_data_aes256(str(data))
                return data
            
            else:
                logger.warning(f"Unknown encryption type: {encryption_type}")
                return data
                
        except Exception as e:
            logger.error(f"Failed to encrypt field: {e}")
            raise ValueError(f"Encryption failed: {str(e)}")
    
    @staticmethod
    def decrypt_sensitive_field(encrypted_data: Any, encryption_type: str) -> Any:
        """
        Decrypt a field based on its encryption type.
        
        Args:
            encrypted_data: The encrypted data
            encryption_type: Type of encryption used
            
        Returns:
            Decrypted data
        """
        if encrypted_data is None:
            return None
        
        try:
            if encryption_type in ["json_encrypt", "json_encrypt_optional"]:
                # Try to decrypt as JSON
                if isinstance(encrypted_data, str) and DataEncryptionService._is_encrypted_data(encrypted_data):
                    decrypted_str = EncryptionManager.decrypt_data_aes256(encrypted_data)
                    return json.loads(decrypted_str)
                return encrypted_data  # Not encrypted or already decrypted
            
            elif encryption_type in ["text_encrypt", "text_encrypt_optional"]:
                # Try to decrypt as text
                if isinstance(encrypted_data, str) and DataEncryptionService._is_encrypted_data(encrypted_data):
                    return EncryptionManager.decrypt_data_aes256(encrypted_data)
                return encrypted_data  # Not encrypted or already decrypted
            
            else:
                return encrypted_data
                
        except Exception as e:
            logger.error(f"Failed to decrypt field: {e}")
            # Return original data if decryption fails (might not be encrypted)
            return encrypted_data
    
    @staticmethod
    def _contains_sensitive_data(data: Any) -> bool:
        """Check if data contains sensitive information that should be encrypted."""
        if not data:
            return False
        
        # Convert to string for analysis
        data_str = json.dumps(data).lower() if not isinstance(data, str) else str(data).lower()
        
        # Keywords that indicate sensitive data
        sensitive_keywords = [
            "api_key", "secret", "password", "token", "key", "credential",
            "auth", "private", "confidential", "sensitive", "sk-", "gsk_",
            "akia", "bearer", "oauth", "jwt"
        ]
        
        return any(keyword in data_str for keyword in sensitive_keywords)
    
    @staticmethod
    def _is_sensitive_text(text: str) -> bool:
        """Check if text contains sensitive information."""
        if not text or len(text) < 10:
            return False
        
        text_lower = text.lower()
        
        # Check for API key patterns
        sensitive_patterns = [
            "sk-",  # OpenAI API keys
            "gsk_",  # Groq API keys
            "akia",  # AWS access keys
            "bearer ",  # Bearer tokens
            "authorization:",  # Auth headers
            "password",  # Password fields
            "secret",  # Secret values
        ]
        
        return any(pattern in text_lower for pattern in sensitive_patterns)
    
    @staticmethod
    def _is_encrypted_data(data: str) -> bool:
        """Check if data appears to be encrypted (base64 encoded)."""
        if not isinstance(data, str) or len(data) < 20:
            return False
        
        try:
            # Check if it's valid base64 and has reasonable length for encrypted data
            import base64
            decoded = base64.b64decode(data.encode())
            return len(decoded) > 44  # Minimum size for AES-256-GCM encrypted data
        except Exception:
            return False
    
    @staticmethod
    async def encrypt_user_data(db: AsyncSession, user_id: str) -> Dict[str, int]:
        """
        Encrypt all sensitive data for a specific user.
        
        Args:
            db: Database session
            user_id: User ID to encrypt data for
            
        Returns:
            Dictionary with count of encrypted records by table
        """
        encryption_counts = {}
        
        try:
            # Encrypt user data
            from app.models.user import User
            
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            
            if user:
                # Encrypt API keys if not already encrypted
                if user.api_keys and not DataEncryptionService._is_encrypted_data(str(user.api_keys)):
                    encrypted_keys = DataEncryptionService.encrypt_sensitive_field(
                        user.api_keys, "json_encrypt"
                    )
                    user.api_keys = {"encrypted_data": encrypted_keys}
                
                # Optionally encrypt hand history paths if they contain sensitive info
                if user.hand_history_paths:
                    encrypted_paths = DataEncryptionService.encrypt_sensitive_field(
                        user.hand_history_paths, "json_encrypt_optional"
                    )
                    if encrypted_paths != user.hand_history_paths:
                        user.hand_history_paths = {"encrypted_data": encrypted_paths}
                
                encryption_counts["users"] = 1
            
            # Encrypt poker hands data
            from app.models.hand import PokerHand
            
            hands_result = await db.execute(
                select(PokerHand).where(PokerHand.user_id == user_id)
            )
            hands = hands_result.scalars().all()
            
            hands_encrypted = 0
            for hand in hands:
                if hand.raw_text and not DataEncryptionService._is_encrypted_data(hand.raw_text):
                    encrypted_text = DataEncryptionService.encrypt_sensitive_field(
                        hand.raw_text, "text_encrypt_optional"
                    )
                    if encrypted_text != hand.raw_text:
                        hand.raw_text = encrypted_text
                        hands_encrypted += 1
            
            encryption_counts["poker_hands"] = hands_encrypted
            
            # Encrypt analysis results
            from app.models.analysis import AnalysisResult
            from app.models.hand import PokerHand
            
            analysis_result = await db.execute(
                select(AnalysisResult)
                .join(PokerHand, AnalysisResult.hand_id == PokerHand.id)
                .where(PokerHand.user_id == user_id)
            )
            analyses = analysis_result.scalars().all()
            
            analyses_encrypted = 0
            for analysis in analyses:
                # Encrypt analysis text if sensitive
                if analysis.analysis_text and not DataEncryptionService._is_encrypted_data(analysis.analysis_text):
                    encrypted_text = DataEncryptionService.encrypt_sensitive_field(
                        analysis.analysis_text, "text_encrypt_optional"
                    )
                    if encrypted_text != analysis.analysis_text:
                        analysis.analysis_text = encrypted_text
                        analyses_encrypted += 1
                
                # Encrypt metadata if sensitive
                if analysis.analysis_metadata:
                    encrypted_metadata = DataEncryptionService.encrypt_sensitive_field(
                        analysis.analysis_metadata, "json_encrypt_optional"
                    )
                    if encrypted_metadata != analysis.analysis_metadata:
                        analysis.analysis_metadata = {"encrypted_data": encrypted_metadata}
                        analyses_encrypted += 1
            
            encryption_counts["analysis_results"] = analyses_encrypted
            
            await db.commit()
            
            logger.info(f"Encrypted sensitive data for user {user_id}: {encryption_counts}")
            return encryption_counts
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to encrypt user data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to encrypt sensitive data: {str(e)}"
            )
    
    @staticmethod
    async def decrypt_user_data(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        Decrypt sensitive data for a specific user for export or viewing.
        
        Args:
            db: Database session
            user_id: User ID to decrypt data for
            
        Returns:
            Dictionary with decrypted user data
        """
        try:
            from app.models.user import User
            
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Decrypt user data
            decrypted_data = {
                "user_info": {
                    "id": str(user.id),
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "is_active": user.is_active,
                    "preferences": user.preferences,
                }
            }
            
            # Decrypt API keys
            if user.api_keys:
                decrypted_keys = DataEncryptionService.decrypt_sensitive_field(
                    user.api_keys, "json_encrypt"
                )
                # Only include provider names, not actual keys for security
                if isinstance(decrypted_keys, dict):
                    decrypted_data["user_info"]["api_providers"] = list(decrypted_keys.keys())
                else:
                    decrypted_data["user_info"]["api_providers"] = []
            
            # Decrypt hand history paths
            if user.hand_history_paths:
                decrypted_paths = DataEncryptionService.decrypt_sensitive_field(
                    user.hand_history_paths, "json_encrypt_optional"
                )
                decrypted_data["user_info"]["hand_history_paths"] = decrypted_paths
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to decrypt user data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to decrypt user data: {str(e)}"
            )
    
    @staticmethod
    async def validate_encryption_status(db: AsyncSession) -> Dict[str, Any]:
        """
        Validate the encryption status of sensitive data across the application.
        
        Returns:
            Dictionary with encryption status report
        """
        try:
            from app.models.user import User
            from app.models.hand import PokerHand
            from app.models.analysis import AnalysisResult
            from sqlalchemy import func
            
            validation_report = {
                "timestamp": datetime.now().isoformat(),
                "tables": {}
            }
            
            # Check users table
            users_result = await db.execute(select(User))
            users = users_result.scalars().all()
            
            users_with_encrypted_keys = 0
            users_with_unencrypted_keys = 0
            
            for user in users:
                if user.api_keys:
                    if DataEncryptionService._is_encrypted_data(str(user.api_keys)):
                        users_with_encrypted_keys += 1
                    else:
                        users_with_unencrypted_keys += 1
            
            validation_report["tables"]["users"] = {
                "total_users": len(users),
                "encrypted_api_keys": users_with_encrypted_keys,
                "unencrypted_api_keys": users_with_unencrypted_keys,
                "encryption_rate": users_with_encrypted_keys / max(len(users), 1) * 100
            }
            
            # Check poker hands table
            hands_count = await db.execute(select(func.count(PokerHand.id)))
            total_hands = hands_count.scalar() or 0
            
            encrypted_hands_count = await db.execute(
                select(func.count(PokerHand.id)).where(
                    PokerHand.raw_text.like('%==%')  # Base64 encoded data typically ends with =
                )
            )
            encrypted_hands = encrypted_hands_count.scalar() or 0
            
            validation_report["tables"]["poker_hands"] = {
                "total_hands": total_hands,
                "encrypted_raw_text": encrypted_hands,
                "encryption_rate": encrypted_hands / max(total_hands, 1) * 100
            }
            
            # Check analysis results table
            analysis_count = await db.execute(select(func.count(AnalysisResult.id)))
            total_analyses = analysis_count.scalar() or 0
            
            encrypted_analysis_count = await db.execute(
                select(func.count(AnalysisResult.id)).where(
                    AnalysisResult.analysis_text.like('%==%')
                )
            )
            encrypted_analyses = encrypted_analysis_count.scalar() or 0
            
            validation_report["tables"]["analysis_results"] = {
                "total_analyses": total_analyses,
                "encrypted_analysis_text": encrypted_analyses,
                "encryption_rate": encrypted_analyses / max(total_analyses, 1) * 100
            }
            
            # Calculate overall encryption score
            total_sensitive_fields = (
                users_with_encrypted_keys + users_with_unencrypted_keys +
                total_hands + total_analyses
            )
            total_encrypted_fields = (
                users_with_encrypted_keys + encrypted_hands + encrypted_analyses
            )
            
            validation_report["overall"] = {
                "total_sensitive_fields": total_sensitive_fields,
                "encrypted_fields": total_encrypted_fields,
                "overall_encryption_rate": total_encrypted_fields / max(total_sensitive_fields, 1) * 100,
                "compliance_status": "COMPLIANT" if total_encrypted_fields / max(total_sensitive_fields, 1) >= 0.95 else "NON_COMPLIANT"
            }
            
            return validation_report
            
        except Exception as e:
            logger.error(f"Failed to validate encryption status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to validate encryption status: {str(e)}"
            )
    
    @staticmethod
    async def encrypt_all_sensitive_data(db: AsyncSession) -> Dict[str, Any]:
        """
        Encrypt all sensitive data across the entire application.
        
        Returns:
            Dictionary with encryption results
        """
        try:
            from app.models.user import User
            from sqlalchemy import func
            
            # Get all users
            users_result = await db.execute(select(User))
            users = users_result.scalars().all()
            
            total_encryption_counts = {
                "users": 0,
                "poker_hands": 0,
                "analysis_results": 0,
                "errors": []
            }
            
            for user in users:
                try:
                    user_counts = await DataEncryptionService.encrypt_user_data(db, str(user.id))
                    for table, count in user_counts.items():
                        total_encryption_counts[table] += count
                except Exception as e:
                    total_encryption_counts["errors"].append(f"User {user.id}: {str(e)}")
            
            logger.info(f"Completed bulk encryption: {total_encryption_counts}")
            return total_encryption_counts
            
        except Exception as e:
            logger.error(f"Failed to encrypt all sensitive data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to encrypt all sensitive data: {str(e)}"
            )
    
    @staticmethod
    def get_encryption_key_info() -> Dict[str, Any]:
        """
        Get information about the encryption keys and algorithms in use.
        
        Returns:
            Dictionary with encryption configuration info
        """
        return {
            "encryption_algorithm": "AES-256-GCM",
            "key_derivation": "PBKDF2-HMAC-SHA256",
            "key_derivation_iterations": 100000,
            "salt_size_bits": 128,
            "nonce_size_bits": 96,
            "tag_size_bits": 128,
            "legacy_algorithm": "Fernet (AES-128-CBC)",
            "password_hashing": "bcrypt" if "bcrypt" in str(type(pwd_context)) else "PBKDF2-SHA256",
            "secure_random_source": "os.urandom",
            "constant_time_comparison": "secrets.compare_digest"
        }


# Import pwd_context for the info function
from app.core.security import pwd_context
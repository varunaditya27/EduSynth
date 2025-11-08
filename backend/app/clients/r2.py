"""
Cloudflare R2 client for object storage operations.
"""
import logging
from typing import Optional

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import settings

logger = logging.getLogger(__name__)


class R2Client:
    """
    Cloudflare R2 storage client using S3-compatible API.
    """
    
    def __init__(self):
        """
        Initialize R2 client with credentials from settings.
        
        Raises:
            ValueError: If required configuration is missing
        """
        if not all([
            settings.CLOUDFLARE_S3_ENDPOINT,
            settings.CLOUDFLARE_S3_ACCESS_KEY,
            settings.CLOUDFLARE_S3_SECRET_KEY,
            settings.CLOUDFLARE_S3_BUCKET,
        ]):
            raise ValueError(
                "Missing required R2 configuration. Check CLOUDFLARE_S3_* environment variables."
            )
        
        self.bucket = settings.CLOUDFLARE_S3_BUCKET
        self.endpoint = settings.CLOUDFLARE_S3_ENDPOINT
        
        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=settings.CLOUDFLARE_S3_ACCESS_KEY,
                aws_secret_access_key=settings.CLOUDFLARE_S3_SECRET_KEY,
                config=BotoConfig(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                ),
            )
        except Exception as e:
            logger.error(f"Failed to initialize R2 client: {e}")
            raise ValueError(f"R2 client initialization failed: {e}")
    
    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload an object to R2.
        
        Args:
            key: Object key (path) in bucket
            data: Binary data to upload
            content_type: MIME type (e.g., "application/pdf")
            metadata: Optional metadata dict
            
        Returns:
            Object key on success
            
        Raises:
            RuntimeError: If upload fails
        """
        try:
            extra_args = {
                "ContentType": content_type,
            }
            
            if metadata:
                extra_args["Metadata"] = metadata
            
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                **extra_args,
            )
            
            logger.info(f"Uploaded object to R2: {key} ({len(data)} bytes)")
            return key
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"R2 upload failed [{error_code}]: {error_msg}")
            raise RuntimeError(f"Failed to upload to R2: {error_msg}")
        
        except BotoCoreError as e:
            logger.error(f"BotoCore error during upload: {e}")
            raise RuntimeError(f"R2 upload error: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error during R2 upload: {e}")
            raise RuntimeError(f"R2 upload failed: {e}")
    
    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 900,
    ) -> str:
        """
        Generate a presigned download URL for an object.
        
        Args:
            key: Object key in bucket
            expires_in: URL expiration time in seconds (default: 15 minutes)
            
        Returns:
            Presigned URL string
            
        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                },
                ExpiresIn=expires_in,
            )
            
            logger.info(f"Generated presigned URL for {key} (expires in {expires_in}s)")
            return url
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"Presigned URL generation failed [{error_code}]: {error_msg}")
            raise RuntimeError(f"Failed to generate presigned URL: {error_msg}")
        
        except BotoCoreError as e:
            logger.error(f"BotoCore error during presigned URL generation: {e}")
            raise RuntimeError(f"Presigned URL generation error: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error during presigned URL generation: {e}")
            raise RuntimeError(f"Presigned URL generation failed: {e}")
    
    def delete_object(self, key: str) -> None:
        """
        Delete an object from R2.
        
        Args:
            key: Object key to delete
            
        Raises:
            RuntimeError: If deletion fails
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted object from R2: {key}")
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"R2 deletion failed [{error_code}]: {error_msg}")
            raise RuntimeError(f"Failed to delete from R2: {error_msg}")
        
        except Exception as e:
            logger.error(f"Unexpected error during R2 deletion: {e}")
            raise RuntimeError(f"R2 deletion failed: {e}")
    
    def object_exists(self, key: str) -> bool:
        """
        Check if an object exists in R2.
        
        Args:
            key: Object key to check
            
        Returns:
            True if object exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise
        except Exception:
            return False


def get_r2_client() -> R2Client:
    """
    Factory function to create R2 client instance.
    
    Returns:
        Configured R2Client instance
    """
    return R2Client()
# backend/app/clients/r2.py

from typing import Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class R2Client:
    """
    Client for interacting with Cloudflare R2 (S3-compatible storage).
    Supports both naming conventions for environment variables.
    """
    
    def __init__(self):
        """
        Initialize R2 client with credentials from settings.
        Settings already handle both CLOUDFLARE_S3_ACCESS_KEY and 
        CLOUDFLARE_S3_ACCESS_KEY_ID naming conventions.
        """
        self.bucket_name = settings.CLOUDFLARE_S3_BUCKET
        
        # Initialize boto3 S3 client with R2 endpoint
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.CLOUDFLARE_S3_ENDPOINT,
            aws_access_key_id=settings.CLOUDFLARE_S3_ACCESS_KEY,
            aws_secret_access_key=settings.CLOUDFLARE_S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto"  # R2 uses 'auto' region
        )
    
    async def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload an object to R2 storage.
        
        Args:
            key: Object key (path) in the bucket
            data: Binary data to upload
            content_type: MIME type of the content
            
        Returns:
            The key of the uploaded object
            
        Raises:
            ClientError: If upload fails
        """
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            return key
        except ClientError as e:
            raise Exception(f"Failed to upload to R2: {str(e)}")
    
    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 300
    ) -> str:
        """
        Generate a presigned URL for downloading an object.
        
        Args:
            key: Object key (path) in the bucket
            expires_in: URL expiration time in seconds (default: 5 minutes)
            
        Returns:
            Presigned URL string
            
        Raises:
            ClientError: If URL generation fails
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
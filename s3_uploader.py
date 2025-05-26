# Option Alpha Framework - S3 Upload Module
# Separate module for S3 upload functionality to keep files smaller

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Optional S3 imports with graceful fallbacks
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

class S3Uploader:
    """
    Handles S3 upload functionality for backtest results.
    Separated from main state manager to keep files smaller and more focused.
    """
    
    def __init__(self, bucket_name: Optional[str] = None, prefix: str = "backtests"):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self._s3_client = None
        self._logger = self._setup_logger()
        
        if bucket_name and S3_AVAILABLE:
            self._init_s3_client()
        elif bucket_name and not S3_AVAILABLE:
            self._logger.warning("S3 bucket specified but boto3 not available. Upload disabled.")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for S3 uploader"""
        logger = logging.getLogger(f"{__name__}.S3Uploader")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _init_s3_client(self) -> None:
        """Initialize S3 client"""
        if not S3_AVAILABLE:
            self._logger.error("boto3 not available. Cannot initialize S3 client.")
            return
            
        try:
            self._s3_client = boto3.client('s3')
            # Test connection
            self._s3_client.head_bucket(Bucket=self.bucket_name)
            self._logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            self._logger.error("AWS credentials not found. S3 upload will be disabled.")
            self._s3_client = None
        except ClientError as e:
            self._logger.error(f"Failed to initialize S3 client: {e}")
            self._s3_client = None
        except Exception as e:
            self._logger.error(f"Unexpected error initializing S3: {e}")
            self._s3_client = None
    
    def is_available(self) -> bool:
        """Check if S3 upload is available"""
        return self._s3_client is not None and self.bucket_name is not None
    
    def upload_directory(self, local_dir: Path, backtest_id: str, 
                        include_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Upload entire directory to S3.
        
        Args:
            local_dir: Local directory path to upload
            backtest_id: Unique identifier for this backtest
            include_patterns: List of file patterns to include (e.g., ['*.csv', '*.json'])
        
        Returns:
            Dictionary with upload results
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'S3 not available',
                'uploaded_files': 0,
                'total_size_mb': 0
            }
        
        try:
            # Create S3 key prefix with timestamp and backtest ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key_prefix = f"{self.prefix}/{timestamp}_{backtest_id}"
            
            uploaded_files = 0
            total_size = 0
            failed_files = []
            
            # Walk through all files in data directory
            for file_path in local_dir.rglob('*'):
                if file_path.is_file():
                    # Apply include patterns if specified
                    if include_patterns:
                        if not any(file_path.match(pattern) for pattern in include_patterns):
                            continue
                    
                    # Calculate relative path for S3 key
                    relative_path = file_path.relative_to(local_dir)
                    s3_key = f"{s3_key_prefix}/{relative_path}"
                    
                    # Upload file
                    try:
                        file_size = file_path.stat().st_size
                        if self._s3_client is not None:
                            self._s3_client.upload_file(
                                str(file_path), 
                                self.bucket_name, 
                                s3_key
                            )
                        else:
                            self._logger.error("S3 client not initialized. Skipping upload.")
                            continue
                        
                        uploaded_files += 1
                        total_size += file_size
                        
                        self._logger.debug(f"Uploaded: {relative_path} -> s3://{self.bucket_name}/{s3_key}")
                        
                    except Exception as e:
                        self._logger.error(f"Failed to upload {file_path}: {e}")
                        failed_files.append(str(relative_path))
                        continue
            
            # Calculate total size in MB
            total_size_mb = total_size / 1024 / 1024
            
            # Log upload summary
            self._logger.info(f"S3 Upload completed: {uploaded_files} files, {total_size_mb:.2f} MB")
            self._logger.info(f"S3 Location: s3://{self.bucket_name}/{s3_key_prefix}/")
            
            if failed_files:
                self._logger.warning(f"Failed to upload {len(failed_files)} files: {failed_files}")
            
            return {
                'success': True,
                'uploaded_files': uploaded_files,
                'total_size_mb': total_size_mb,
                's3_location': f"s3://{self.bucket_name}/{s3_key_prefix}/",
                'upload_time': datetime.now().isoformat(),
                'failed_files': failed_files
            }
            
        except Exception as e:
            self._logger.error(f"S3 upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'uploaded_files': 0,
                'total_size_mb': 0
            }
    
    def upload_file(self, local_file: Path, s3_key: str) -> bool:
        """
        Upload a single file to S3.
        
        Args:
            local_file: Path to local file
            s3_key: S3 key for the uploaded file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            self._logger.error("S3 not available for file upload")
            return False
        
        try:
            if self._s3_client is not None:
                self._s3_client.upload_file(str(local_file), self.bucket_name, s3_key)
            else:
                self._logger.error("S3 client not initialized. Skipping upload.")
                return False
                
            self._logger.info(f"File uploaded: {local_file} -> s3://{self.bucket_name}/{s3_key}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to upload file {local_file}: {e}")
            return False
    
    def create_upload_manifest(self, upload_result: Dict[str, Any], local_dir: Path) -> Path:
        """
        Create a manifest file with upload details.
        
        Args:
            upload_result: Result from upload_directory
            local_dir: Local directory that was uploaded
            
        Returns:
            Path to created manifest file
        """
        try:
            manifest = {
                'upload_timestamp': datetime.now().isoformat(),
                'local_directory': str(local_dir),
                'bucket': self.bucket_name,
                'prefix': self.prefix,
                's3_location': upload_result.get('s3_location'),
                'uploaded_files': upload_result.get('uploaded_files', 0),
                'total_size_mb': upload_result.get('total_size_mb', 0),
                'failed_files': upload_result.get('failed_files', []),
                'success': upload_result.get('success', False)
            }
            
            manifest_file = local_dir / "s3_upload_manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self._logger.info(f"Upload manifest created: {manifest_file}")
            return manifest_file
            
        except Exception as e:
            self._logger.error(f"Failed to create upload manifest: {e}")
            raise

def create_s3_uploader(bucket_name: Optional[str] = None, prefix: str = "backtests") -> S3Uploader:
    """Factory function to create S3 uploader with error handling"""
    try:
        return S3Uploader(bucket_name, prefix)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create S3 uploader: {e}")
        # Return a disabled uploader
        return S3Uploader(None, prefix)
"""Service for processing CSV files with campaign recipients."""

import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.csv_schema import CSVRecipient, CSVUploadResponse, CSVValidationError

settings = get_settings()
logger = get_logger(__name__)

# Ensure uploads directory exists
UPLOADS_DIR = Path("data/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class CSVService:
    """
    Service for processing CSV files with campaign recipients.
    
    Handles CSV parsing, validation, and message creation.
    """

    def __init__(self):
        """Initialize CSV service."""
        self.uploads_dir = UPLOADS_DIR

    def validate_csv_file(self, file_path: str) -> CSVUploadResponse:
        """
        Validate a CSV file and extract recipients.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            CSVUploadResponse with validation results
        """
        errors: List[Dict[str, str]] = []
        valid_recipients: List[CSVRecipient] = []
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Check required column
            required_column = "Recipient-Phone-Number"
            if required_column not in df.columns:
                return CSVUploadResponse(
                    filename=os.path.basename(file_path),
                    total_rows=len(df),
                    valid_rows=0,
                    invalid_rows=len(df),
                    errors=[{
                        "row": 0,
                        "column": "file",
                        "error": f"Required column '{required_column}' not found",
                    }],
                )
            
            # Process each row
            for index, row in df.iterrows():
                row_num = index + 2  # +2 because index is 0-based and CSV has header
                
                try:
                    # Extract phone number
                    phone = str(row[required_column]).strip()
                    
                    # Extract template variables (all other columns)
                    variables = {}
                    for col in df.columns:
                        if col != required_column:
                            value = row[col]
                            if pd.notna(value):
                                variables[col] = str(value).strip()
                    
                    # Validate recipient
                    recipient = CSVRecipient(
                        phone=phone,
                        variables=variables,
                    )
                    
                    valid_recipients.append(recipient)
                    
                except Exception as e:
                    errors.append({
                        "row": row_num,
                        "column": required_column,
                        "value": str(row.get(required_column, "")),
                        "error": str(e),
                    })
            
            return CSVUploadResponse(
                filename=os.path.basename(file_path),
                total_rows=len(df),
                valid_rows=len(valid_recipients),
                invalid_rows=len(errors),
                errors=errors,
                file_path=file_path,
            )
            
        except Exception as e:
            logger.error(
                "Error validating CSV file",
                file_path=file_path,
                error=str(e),
                exc_info=True,
            )
            return CSVUploadResponse(
                filename=os.path.basename(file_path),
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                errors=[{
                    "row": 0,
                    "column": "file",
                    "error": f"Error reading CSV file: {str(e)}",
                }],
            )

    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(filename).suffix
        safe_filename = f"{timestamp}_{Path(filename).stem}{file_ext}"
        
        file_path = self.uploads_dir / safe_filename
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(
            "File saved",
            filename=filename,
            saved_path=str(file_path),
        )
        
        return str(file_path)

    def parse_csv_recipients(self, file_path: str) -> List[CSVRecipient]:
        """
        Parse CSV file and return list of valid recipients.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of CSVRecipient objects
            
        Raises:
            ValueError: If CSV file is invalid
        """
        try:
            df = pd.read_csv(file_path)
            
            required_column = "Recipient-Phone-Number"
            if required_column not in df.columns:
                raise ValueError(f"Required column '{required_column}' not found")
            
            recipients = []
            for _, row in df.iterrows():
                try:
                    phone = str(row[required_column]).strip()
                    
                    # Extract template variables
                    variables = {}
                    for col in df.columns:
                        if col != required_column:
                            value = row[col]
                            if pd.notna(value):
                                variables[col] = str(value).strip()
                    
                    recipient = CSVRecipient(
                        phone=phone,
                        variables=variables,
                    )
                    
                    recipients.append(recipient)
                    
                except Exception as e:
                    logger.warning(
                        "Skipping invalid row",
                        row=row,
                        error=str(e),
                    )
                    continue
            
            return recipients
            
        except Exception as e:
            logger.error(
                "Error parsing CSV file",
                file_path=file_path,
                error=str(e),
                exc_info=True,
            )
            raise ValueError(f"Error parsing CSV file: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.info("File deleted", file_path=file_path)
                return True
            return False
        except Exception as e:
            logger.error(
                "Error deleting file",
                file_path=file_path,
                error=str(e),
            )
            return False


# Singleton instance
_csv_service: Optional[CSVService] = None


def get_csv_service() -> CSVService:
    """
    Get CSV service instance (singleton).
    
    Returns:
        CSVService instance
    """
    global _csv_service
    if _csv_service is None:
        _csv_service = CSVService()
    return _csv_service


from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from database.session import get_db
from database.models import Integration
from decorators.jwt_decorator import jwt_authorization

from fastapi import UploadFile, File
import pandas as pd
import io

router = APIRouter()


# ---------------------------
# Utility Function for Response
# ---------------------------
def response_formatter(status_code: int, message: str, data: Optional[Any] = None, error_code: Optional[str] = None):
    return {
        "status_code": status_code,
        "error_code": error_code,
        "message": message,
        "data": data
    }


# ---------------------------
# Pydantic Models
# ---------------------------
class IntegrationCreate(BaseModel):
    integration_key: str
    account_id: int
    private_key_file: str
    email: EmailStr
    status: str  # 'active', 'inactive', 'pending', 'failed'


class IntegrationResponse(BaseModel):
    integration_id: int
    integration_key: str
    account_id: int
    email: EmailStr
    status: str

    class Config:
        from_attributes = True

# ---------------------------
# BULK UPLOAD Integrations (POST)
# ---------------------------
@router.post("/integrations/bulk-upload")
def bulk_upload_integrations(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token_data: dict = Depends(jwt_authorization)
):
    # Only admins can bulk upload
    if not token_data.get("is_admin"):
        return {
            "status_code": 403,
            "error_code": "FORBIDDEN",
            "message": "Permission denied",
            "data": None
        }

    # Read Excel file
    try:
        contents = file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
    except Exception:
        return {
            "status_code": 400,
            "error_code": "INVALID_FILE",
            "message": "Invalid Excel file format",
            "data": None
        }

    # Required columns
    required_columns = {"Integration Key", "User ID", "Account ID", "Email"}
    if not required_columns.issubset(set(df.columns)):
        return {
            "status_code": 400,
            "error_code": "MISSING_COLUMNS",
            "message": "Excel file must contain Integration Key, User ID, Account ID, Email columns",
            "data": None
        }

    success_count = 0
    failed_records = []

    for _, row in df.iterrows():
        try:
            # Validate data
            integration_key = str(row["Integration Key"]).strip()
            user_id = int(row["User ID"])
            account_id = int(row["Account ID"])
            email = str(row["Email"]).strip()

            if not integration_key or not email:
                raise ValueError("Invalid data: Empty Integration Key or Email")

            # Create integration record
            new_integration = Integration(
                integration_key=integration_key,
                user_id=user_id,
                account_id=account_id,
                email=email,
                status="active"  # Default status
            )
            db.add(new_integration)
            success_count += 1
        except Exception as e:
            failed_records.append({"row": row.to_dict(), "error": str(e)})

    db.commit()

    return {
        "status_code": 200,
        "error_code": None,
        "message": f"Successfully uploaded {success_count} integrations",
        "data": {"failed_records": failed_records} if failed_records else None
    }


# ---------------------------
# CREATE Integration (POST)
# ---------------------------
@router.post("/integrations", response_model=Dict)
def create_integration(
    integration_data: IntegrationCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(jwt_authorization)
):
    user_id = token_data.get("user_id")
    if not user_id:
        return response_formatter(401, "Unauthorized", error_code="AUTH_401")

    new_integration = Integration(
        integration_key=integration_data.integration_key,
        user_id=user_id,
        account_id=integration_data.account_id,
        private_key_file=integration_data.private_key_file,
        email=integration_data.email,
        status=integration_data.status,
    )

    db.add(new_integration)
    db.commit()
    db.refresh(new_integration)

    return response_formatter(201, "Integration created successfully", new_integration)


# ---------------------------
# GET All Integrations (GET)
# ---------------------------
@router.get("/get-all-integrations", response_model=Dict)
def get_integrations(
    db: Session = Depends(get_db),
    token_data: dict = Depends(jwt_authorization)
):
    if not token_data.get("is_admin"):
        return response_formatter(403, "Permission denied", error_code="PERMISSION_403")

    integrations = db.query(Integration).all()

    if not integrations:
        return response_formatter(404, "No integrations found", error_code="DATA_404")

    return response_formatter(200, "Integrations retrieved successfully", integrations)


# ---------------------------
# GET Single Integration (GET)
# ---------------------------
@router.get("/get-integrations/{integration_id}", response_model=Dict)
def get_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(jwt_authorization)
):
    integration = db.query(Integration).filter(Integration.integration_id == integration_id).first()

    if not integration:
        return response_formatter(404, "Integration not found", error_code="DATA_404")

    if not token_data.get("is_admin") and token_data["user_id"] != integration.user_id:
        return response_formatter(403, "Access denied", error_code="PERMISSION_403")

    return response_formatter(200, "Integration retrieved successfully", integration)


# ---------------------------
# UPDATE Integration (PUT)
# ---------------------------
@router.put("/edit-integrations/{integration_id}", response_model=Dict)
def update_integration(
    integration_id: int,
    integration_data: IntegrationCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(jwt_authorization)
):
    integration = db.query(Integration).filter(Integration.integration_id == integration_id).first()

    if not integration:
        return response_formatter(404, "Integration not found", error_code="DATA_404")

    if not token_data.get("is_admin") and token_data["user_id"] != integration.user_id:
        return response_formatter(403, "Access denied", error_code="PERMISSION_403")

    integration.integration_key = integration_data.integration_key
    integration.account_id = integration_data.account_id
    integration.private_key_file = integration_data.private_key_file
    integration.email = integration_data.email
    integration.status = integration_data.status

    db.commit()
    db.refresh(integration)

    return response_formatter(200, "Integration updated successfully", integration)


# ---------------------------
# DELETE Integration (DELETE)
# ---------------------------
@router.delete("/delete-integrations/{integration_id}", response_model=Dict)
def delete_integration(
    integration_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(jwt_authorization)
):
    integration = db.query(Integration).filter(Integration.integration_id == integration_id).first()

    if not integration:
        return response_formatter(404, "Integration not found", error_code="DATA_404")

    if not token_data.get("is_admin") and token_data["user_id"] != integration.user_id:
        return response_formatter(403, "Access denied", error_code="PERMISSION_403")

    db.delete(integration)
    db.commit()

    return response_formatter(200, "Integration deleted successfully")


# ---------------------------
# TOGGLE Integration Status (PATCH)
# ---------------------------
@router.patch("/integrations/{integration_id}/toggle-status", response_model=Dict)
def toggle_integration_status(
    integration_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(jwt_authorization)
):
    integration = db.query(Integration).filter(Integration.integration_id == integration_id).first()

    if not integration:
        return response_formatter(404, "Integration not found", error_code="DATA_404")

    # Only the owner or admin can change status
    if not token_data.get("is_admin") and token_data["user_id"] != integration.user_id:
        return response_formatter(403, "Access denied", error_code="PERMISSION_403")

    # Toggle status
    integration.status = "inactive" if integration.status == "active" else "active"
    
    db.commit()
    db.refresh(integration)

    return response_formatter(
        200,
        f"Integration status updated to {integration.status}",
        data={"integration_id": integration.integration_id, "new_status": integration.status}
    )
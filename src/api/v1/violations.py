# src/api/v1/violations.py
import os
import uuid
import shutil
from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from typing import List, Optional

from src.schemas import ViolationReportCreate, ViolationReportUpdate, ViolationReportResponse
from src.models import User
from src.services.violation_service import ViolationService
from src.api.deps import get_violation_service, get_current_user, require_role
from src.services.ai_pipeline import process_violation_image

router = APIRouter(prefix="/violations", tags=["violations"])

@router.get("", response_model=List[ViolationReportResponse])
def list_violations(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    violation_service: ViolationService = Depends(get_violation_service)
):
    return violation_service.get_violations(user=current_user, status_filter=status_filter)

@router.post("", response_model=ViolationReportResponse, status_code=status.HTTP_201_CREATED)
def create_violation(
    report_in: ViolationReportCreate,
    current_user: User = Depends(get_current_user),
    violation_service: ViolationService = Depends(get_violation_service)
):
    return violation_service.create_report(report_in=report_in, user=current_user)

@router.post("/upload")
def upload_violation_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    media_dir = os.path.join(root_dir, "media", "citizen_reports")
    os.makedirs(media_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
         file_ext = ".jpg"
         
    unique_filename = f"uploaded_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(media_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        ai_res = process_violation_image(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không tìm thấy biển số xe hợp lệ trong ảnh. Vui lòng chọn ảnh khác rõ nét hơn."
        )

    plate = ai_res.get("vehicle_plate")
    if not plate or plate in ["Không thể nhận diện", "UNKNOWN"]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        annotated_url = ai_res.get("annotated_url")
        if annotated_url:
            annotated_filename = os.path.basename(annotated_url)
            annotated_path = os.path.join(media_dir, annotated_filename)
            if os.path.exists(annotated_path):
                try:
                    os.remove(annotated_path)
                except:
                    pass

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không tìm thấy biển số xe hợp lệ trong ảnh. Vui lòng chọn ảnh khác rõ nét hơn."
        )
        
    return {
        "image_url": f"/media/citizen_reports/{unique_filename}",
        "annotated_url": ai_res.get("annotated_url"),
        "vehicle_plate": ai_res.get("vehicle_plate"),
        "confidence": ai_res.get("confidence")
    }

@router.put("/{violation_id}/status", response_model=ViolationReportResponse)
def update_violation_status(
    violation_id: int,
    update_in: ViolationReportUpdate,
    current_user: User = Depends(require_role(["authority"])),
    violation_service: ViolationService = Depends(get_violation_service)
):
    return violation_service.update_status(violation_id=violation_id, update_in=update_in, user=current_user)


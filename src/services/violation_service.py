# src/services/violation_service.py
import datetime
import random
import os
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional
from fastapi import HTTPException, status

from src.models import ViolationReport, User
from src.schemas import ViolationReportCreate, ViolationReportUpdate
from src.repositories.violation_repository import IViolationRepository
from src.services.camera_service import ICameraService

class IViolationService(ABC):
    @abstractmethod
    def get_violations(self, user: User, status_filter: Optional[str] = None) -> List[ViolationReport]:
        pass

    @abstractmethod
    def create_report(self, report_in: ViolationReportCreate, user: User) -> ViolationReport:
        pass

    @abstractmethod
    def update_status(self, violation_id: int, update_in: ViolationReportUpdate, user: User) -> ViolationReport:
        pass

    @abstractmethod
    def simulate_ai_violation(self) -> ViolationReport:
        pass

class ViolationService(IViolationService):
    def __init__(self, violation_repo: IViolationRepository, camera_service: ICameraService):
        self.violation_repo = violation_repo
        self.camera_service = camera_service

    def _broadcast_new_violation(self, created: ViolationReport):
        from src.core.websocket_manager import manager
        
        report_data = {
            "id": created.id,
            "vehicle_plate": created.vehicle_plate,
            "violation_type": created.violation_type,
            "latitude": created.latitude,
            "longitude": created.longitude,
            "image_url": created.image_url,
            "reporter_role": created.reporter_role,
            "reporter_name": created.reporter_name,
            "status": created.status,
            "duration_seconds": created.duration_seconds,
            "violation_time": created.violation_time.isoformat() if created.violation_time else None
        }
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(manager.broadcast({
                "type": "NEW_VIOLATION",
                "data": report_data
            }))
        except RuntimeError:
            pass

    def get_violations(self, user: User, status_filter: Optional[str] = None) -> List[ViolationReport]:
        reporter_name = user.full_name if user.role == "citizen" else None
        return self.violation_repo.get_list(
            reporter_role=user.role,
            reporter_name=reporter_name,
            status_filter=status_filter
        )

    def create_report(self, report_in: ViolationReportCreate, user: User) -> ViolationReport:
        reporter_role = user.role
        reporter_name = user.full_name
        
        # Citizens reports are pending verification, system/AI reports are pre-verified or logged
        status_val = "pending" if user.role == "citizen" else "verified"
        
        image_url = report_in.image_url
        vehicle_plate = report_in.vehicle_plate.upper() if report_in.vehicle_plate else "UNKNOWN"
        
        # Run AI annotation on the image if uploaded
        if image_url:
            filename = os.path.basename(image_url)
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            abs_image_path = os.path.join(root_dir, "media", filename)
            if not os.path.exists(abs_image_path):
                abs_image_path = os.path.join(root_dir, "media", "citizen_reports", filename)
            if not os.path.exists(abs_image_path):
                abs_image_path = os.path.join(root_dir, "media", "cameras", filename)
                
            if os.path.exists(abs_image_path):
                from src.services.ai_pipeline import process_violation_image
                try:
                    res = process_violation_image(abs_image_path)
                    image_url = res["annotated_url"]
                    if not vehicle_plate or vehicle_plate == "UNKNOWN":
                        vehicle_plate = res["vehicle_plate"]
                except Exception:
                    pass
        
        new_report = ViolationReport(
            vehicle_plate=vehicle_plate,
            violation_type=report_in.violation_type,
            latitude=report_in.latitude,
            longitude=report_in.longitude,
            image_url=image_url,
            reporter_role=reporter_role,
            reporter_name=reporter_name,
            status=status_val,
            duration_seconds=report_in.duration_seconds,
            violation_time=datetime.datetime.utcnow()
        )
        created_report = self.violation_repo.create(new_report)
        
        # Log to camera service if it came from the AI camera
        if reporter_role == "ai_system":
            self.camera_service.log(
                f"Đã tạo bản ghi vi phạm: {created_report.vehicle_plate} ({created_report.violation_type})"
            )
            
        self._broadcast_new_violation(created_report)
        return created_report
 
    def update_status(self, violation_id: int, update_in: ViolationReportUpdate, user: User) -> ViolationReport:
        report = self.violation_repo.get(violation_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy bản ghi vi phạm."
            )
            
        updated = self.violation_repo.update(report, {"status": update_in.status})
        
        self.camera_service.log(
            f"[QUẢN TRỊ] Cán bộ {user.full_name} đã cập nhật trạng thái: {updated.vehicle_plate} -> {update_in.status.upper()}"
        )
        return updated
 
    def simulate_ai_violation(self, camera_id: int = None, violation_type: str = None) -> ViolationReport:
        is_active = True
        lat = 10.7745
        lon = 106.7025
        reporter_name = "Hệ thống AI"
        
        if camera_id:
            cam = next((c for c in self.camera_service.cameras if c["id"] == str(camera_id)), None)
            if cam:
                is_active = cam.get("is_active", True)
                lat = cam["latitude"]
                lon = cam["longitude"]
                reporter_name = cam["name"]
        else:
            camera_status = self.camera_service.get_status()
            is_active = camera_status["is_active"]
            lat = camera_status["location"]["lat"]
            lon = camera_status["location"]["lon"]

        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể giả lập vi phạm khi camera đang tắt."
            )
            
        image_filename = random.choice(["violation_sidewalk.jpg", "violation_no_parking_sign.jpg", "violation_double_parked.jpg"])
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        image_path = os.path.join(root_dir, "media", "citizen_reports", image_filename)
        
        from src.services.ai_pipeline import process_violation_image, IMAGE_METADATA_MAPPING
        
        res = process_violation_image(image_path)
        meta = IMAGE_METADATA_MAPPING.get(image_filename, {})
        
        lat = meta.get("latitude", lat + random.uniform(-0.0005, 0.0005))
        lon = meta.get("longitude", lon + random.uniform(-0.0005, 0.0005))
        v_type = violation_type if violation_type else meta.get("violation_type", "Đỗ xe đè vỉa hè")
        duration = random.randint(180, 1200)
        
        new_report = ViolationReport(
            vehicle_plate=res["vehicle_plate"],
            violation_type=v_type,
            latitude=lat,
            longitude=lon,
            image_url=res["annotated_url"],
            reporter_role="ai_system",
            reporter_name=reporter_name,
            status="pending",
            duration_seconds=duration,
            violation_time=datetime.datetime.utcnow()
        )
        created = self.violation_repo.create(new_report)
        
        self.camera_service.log(
            f"[AI DETECTED] Phương tiện {res['vehicle_plate']} đỗ trái phép ({v_type}). Độ tin cậy AI: {int(res['confidence']*100)}%"
        )
        self._broadcast_new_violation(created)
        return created

import datetime
from sqlalchemy.orm import Session
import models

def log_verification_action(db: Session, action: str, user_id: int = None, ip_address: str = "127.0.0.1", status: str = "success", details: str = None):
    try:
        log_entry = models.VerificationLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            status=status,
            details=details,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        try:
            import blast_gateway
            blast_gateway.gateway.sync_verification_log({
                "user_id": user_id,
                "action": action,
                "ip_address": ip_address,
                "status": status,
                "details": details,
            })
        except Exception:
            pass
        return log_entry
    except Exception as e:
        db.rollback()
        print(f"Error logging verification action: {e}")
        return None

def audit_verification_status(db: Session) -> dict:
    total_users = db.query(models.User).count()
    verified_users = db.query(models.User).filter(models.User.is_verified == True).count()
    total_requests = db.query(models.RequestItem).count()
    total_logs = db.query(models.VerificationLog).count()
    
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "total_users": total_users,
        "verified_users": verified_users,
        "total_requests": total_requests,
        "total_logs": total_logs
    }

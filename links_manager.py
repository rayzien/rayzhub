import secrets
import string
from sqlalchemy.orm import Session
import models, schemas

def generate_short_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_short_link(db: Session, title: str, target_url: str) -> models.LinkItem:
    short_code = generate_short_code()
    # Ensure unique short code
    while db.query(models.LinkItem).filter(models.LinkItem.short_code == short_code).first():
        short_code = generate_short_code()
        
    link_item = models.LinkItem(
        title=title,
        target_url=target_url,
        short_code=short_code,
        clicks=0
    )
    db.add(link_item)
    db.commit()
    db.refresh(link_item)
    try:
        import blast_gateway
        blast_gateway.gateway.sync_link({
            "title": link_item.title,
            "target_url": link_item.target_url,
            "short_code": link_item.short_code,
            "clicks": link_item.clicks,
        })
    except Exception:
        pass
    return link_item

def record_link_click(db: Session, short_code: str) -> models.LinkItem:
    link = db.query(models.LinkItem).filter(models.LinkItem.short_code == short_code).first()
    if link:
        link.clicks += 1
        db.commit()
        db.refresh(link)
        try:
            import blast_gateway
            blast_gateway.gateway.sync_click(link.short_code, link.clicks)
        except Exception:
            pass
    return link

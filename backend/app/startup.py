
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.database import SessionLocal
from app.models.user import User

logger = logging.getLogger("accessiq.startup")

BACKEND_DIR = Path(__file__).resolve().parent.parent


def run_migrations() -> None:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")
    logger.info("Migrations up to date.")


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        has_users = db.query(User).first() is not None
    finally:
        db.close()

    if has_users:
        logger.info("Database already has data; skipping auto-seed.")
        return

    logger.info("Database is empty — seeding the demo roster (admin, managers, sample team).")
    from app.seed import main as seed_main

    seed_main()


def run_startup_tasks() -> None:
    run_migrations()
    try:
        seed_if_empty()
    except Exception:
        logger.exception("Auto-seed failed; the app will still run against an empty database.")

from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo

from backend.integrations.imap_fetcher import IMAPFetcher
from backend.services.ingestion.ingest import ingest_email
from backend.services.tracking.tracker import process_email
from backend.services.compliance.monitor import check_daily_update_compliance
from backend.core.config import EMAIL_HOST, EMAIL_USER, EMAIL_PASS
from backend.core.logger import logger


def fetch_and_process():

    logger.info("Scheduler cycle started")

    fetcher = IMAPFetcher(EMAIL_HOST, EMAIL_USER, EMAIL_PASS)
    emails = fetcher.fetch_all_emails()

    new_count = 0
    dup_count = 0

    for e in emails:

        inserted = ingest_email(
            e["sender"],
            e["subject"],
            e["body"],
            e["message_id"],
            e.get("email_date")
        )

        if inserted:
            new_count += 1
            process_email(e["message_id"])
        else:
            dup_count += 1

    logger.info(f"New emails added: {new_count}")
    logger.info(f"Duplicates skipped: {dup_count}")
    logger.info("Scheduler cycle finished")


def start_scheduler():

    scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Kolkata"))

    # Fetch inbox every 5 minutes
    scheduler.add_job(
        fetch_and_process,
        trigger="interval",
        minutes=1,
        id="email_fetch_job",
        replace_existing=True
    )

    # Compliance check (daily)
    scheduler.add_job(
        check_daily_update_compliance,
        trigger="cron",
        hour=8,
        minute=50,
        misfire_grace_time=300,
        id="compliance_job",
        replace_existing=True
    )

    scheduler.start()

    logger.info("Scheduler started with email fetch + compliance monitoring")
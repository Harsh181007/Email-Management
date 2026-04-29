from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from sqlalchemy import func

from backend.core.database import SessionLocal
from backend.domain.models import Email, ComplianceRecord
from backend.domain.interns import REGISTERED_INTERNS
from backend.integrations.mail_sender import send_email
from backend.core.logger import logger

IST = ZoneInfo("Asia/Kolkata")
DEADLINE_HOUR = 9


def check_daily_update_compliance():

    db = SessionLocal()
    now = datetime.now(IST)

    # Correct way to get today's date
    today_date = now.date()

    for intern_email in REGISTERED_INTERNS:

        logger.info(f"Checking compliance for {intern_email}")

        latest_email = (
            db.query(Email)
            .filter(func.lower(Email.sender) == intern_email.lower())
            .order_by(Email.created_at.desc())
            .first()
        )

        if not latest_email:
            logger.info(f"No updates ever received from {intern_email}")
            continue

        last_update_date = latest_email.created_at.astimezone(IST).date()

        expected_date = last_update_date + timedelta(days=1)

        deadline = datetime.combine(
            expected_date,
            time(hour=DEADLINE_HOUR),
            tzinfo=IST
        )

        if now > deadline:

            report_date = expected_date.strftime("%d/%m/%y")

            # Check if reminder already sent today
            existing_record = (
                db.query(ComplianceRecord)
                .filter(func.lower(ComplianceRecord.intern_email) == intern_email.lower())
                .filter(func.date(ComplianceRecord.created_at) == today_date)
                .first()
            )

            if existing_record:
                logger.info(f"Reminder already sent today for {intern_email}")
                continue

            logger.info(
                f"{intern_email} missed update deadline. "
                f"Last update: {last_update_date}"
            )

            send_email(
                to_email=intern_email,
                subject="Reminder: Daily Update Missing",
                body=(
                    f"Dear Intern,\n\n"
                    f"We have not received your daily update after "
                    f"{last_update_date.strftime('%d %B %Y')}.\n\n"
                    f"Please send your update before 11 AM tomorrow.\n\n"
                    f"Regards,\n"
                    f"Intern Monitoring System"
                )
            )

            record = ComplianceRecord(
                intern_email=intern_email,
                report_date=report_date,
                reminder_sent=1
            )

            db.add(record)
            db.commit()

            logger.info(f"Reminder sent to {intern_email}")

            print("Checking:", intern_email)
            print("Last update:", last_update_date)
            print("Expected deadline:", deadline)
            print("Current time:", now)

    db.close()
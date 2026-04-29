# backend/summariser/summarise.py

import re
from datetime import datetime
# ---------------------------------------------------------
# STRUCTURED DETECTION
# ---------------------------------------------------------

def is_structured_report(body: str) -> bool:
    """
    Detect structured intern report template robustly.
    """

    body_lower = body.lower()

    required_sections = [
        "major project work",
        "general project work",
        "other projects",
        "planned work"
    ]

    matches = sum(1 for section in required_sections if section in body_lower)

    return matches >= 3


# ---------------------------------------------------------
# TIME EXTRACTION
# ---------------------------------------------------------

def extract_total_time(body: str) -> str:
    """
    Extract and sum HH:MM values.
    """

    matches = re.findall(r"(\d{2})\s*:\s*(\d{2})", body)

    total_minutes = 0

    for hours, minutes in matches:
        total_minutes += int(hours) * 60 + int(minutes)

    total_hours = total_minutes // 60
    remaining_minutes = total_minutes % 60

    return f"{total_hours:02d}:{remaining_minutes:02d}"


# ---------------------------------------------------------
# SECTION EXTRACTION
# ---------------------------------------------------------

def extract_section(body: str, section_name: str) -> str:
    """
    Extract text of a given section.
    """

    pattern = rf"{section_name}\s*[-–:]?(.*?)(?=(major project work|general project work|other projects|any challenge|planned work|$))"

    match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)

    if match:
        text = match.group(1).strip()
        return re.sub(r"\s+", " ", text)

    return ""


# ---------------------------------------------------------
# DETERMINISTIC SUMMARY
# ---------------------------------------------------------

def generate_structured_summary(body: str) -> str:
    """
    Build deterministic structured summary.
    """

    major = extract_section(body, "major project work")
    general = extract_section(body, "general project work")
    other = extract_section(body, "other projects")
    challenge = extract_section(body, "any challenge")

    total_time = extract_total_time(body)

    summary_parts = []

    if major:
        summary_parts.append(f"Completed major tasks including {major}.")

    if general:
        summary_parts.append(f"Additionally worked on {general}.")

    if other:
        summary_parts.append(f"Other tasks included {other}.")

    if challenge and challenge.strip() not in ["-", "—"]:
        summary_parts.append(f"Challenges faced: {challenge}.")

    summary_parts.append(f"Total logged time: {total_time}.")

    return " ".join(summary_parts)


# ---------------------------------------------------------
# MAIN ROUTER
# ---------------------------------------------------------

def summarise_email(body: str, llm_fallback=None) -> str:
    """
    Structured → deterministic summary
    Plain text → LLM fallback
    """

    if is_structured_report(body):
        return generate_structured_summary(body)

    # 🔥 Remove DD/MM/YY before sending to LLM to prevent hallucinated US dates
    cleaned_body = re.sub(r"\b\d{2}/\d{2}/\d{2}\b", "", body)

    if llm_fallback:
        return llm_fallback(cleaned_body)

    return cleaned_body[:300]

def extract_report_date(body: str):
    """
    Extracts DD/MM/YY from structured template.
    """

    match = re.search(r"\b(\d{2}/\d{2}/\d{2})\b", body)

    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, "%d/%m/%y").date()

    return None
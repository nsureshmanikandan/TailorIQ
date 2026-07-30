"""Job description management API routes.

Provides endpoints for:
- POST /jobs/text — Submit JD as pasted text
- POST /jobs/url — Fetch JD from a URL (strips HTML)
"""

import logging
import uuid
from typing import Annotated

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.db import JobDescription
from app.schemas.job import JDResponse, JDTextInput, JDUrlInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/text", response_model=JDResponse, status_code=status.HTTP_201_CREATED)
async def submit_jd_text(
    body: JDTextInput,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> JDResponse:
    """Submit a job description as pasted text.

    Stores the raw text for later analysis pipeline execution.
    """
    user_id = uuid.UUID(user["user_id"])

    jd = JobDescription(
        user_id=user_id,
        source_type="text",
        raw_text=body.text,
    )
    db.add(jd)
    await db.flush()

    logger.info("JD text submitted: %s (user=%s)", jd.id, user_id)

    return JDResponse(
        jd_id=jd.id,
        raw_text=jd.raw_text,
        source_type=jd.source_type,
        source_url=None,
        created_at=jd.created_at,
    )


@router.post("/url", response_model=JDResponse, status_code=status.HTTP_201_CREATED)
async def fetch_jd_from_url(
    body: JDUrlInput,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> JDResponse:
    """Fetch a job description from a URL.

    Downloads the page content, strips HTML tags, and extracts
    the job description text. Supports common job board formats.
    """
    user_id = uuid.UUID(user["user_id"])
    url_str = str(body.url)

    # Fetch the URL content
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; ResumeJDMatch/1.0)",
            },
        ) as client:
            response = await client.get(url_str)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Timeout fetching the URL. Please try again or paste the text directly.",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to fetch URL (HTTP {e.response.status_code}). Please paste the text directly.",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to connect to the URL. Please paste the text directly.",
        )

    # Parse HTML and extract text
    html_content = response.text
    raw_text = _extract_text_from_html(html_content)

    if len(raw_text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract sufficient text from the URL. Please paste the job description directly.",
        )

    jd = JobDescription(
        user_id=user_id,
        source_type="url",
        source_url=url_str,
        raw_text=raw_text,
    )
    db.add(jd)
    await db.flush()

    logger.info("JD fetched from URL: %s (user=%s)", jd.id, user_id)

    return JDResponse(
        jd_id=jd.id,
        raw_text=jd.raw_text,
        source_type=jd.source_type,
        source_url=url_str,
        created_at=jd.created_at,
    )


def _extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML content.

    Removes scripts, styles, navigation, and other non-content elements.
    Preserves paragraph structure with newlines.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for element in soup.find_all(
        ["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]
    ):
        element.decompose()

    # Try to find job description-specific containers first
    content_selectors = [
        {"class_": "job-description"},
        {"class_": "description"},
        {"class_": "job-details"},
        {"id": "job-description"},
        {"id": "description"},
        {"role": "main"},
        {"class_": "content"},
    ]

    for selector in content_selectors:
        container = soup.find("div", **selector) or soup.find("section", **selector)
        if container and len(container.get_text(strip=True)) > 100:
            text = container.get_text(separator="\n", strip=True)
            return _clean_text(text)

    # Fallback: extract from body
    body = soup.find("body")
    if body:
        text = body.get_text(separator="\n", strip=True)
        return _clean_text(text)

    return _clean_text(soup.get_text(separator="\n", strip=True))


def _clean_text(text: str) -> str:
    """Clean extracted text by removing excessive whitespace."""
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)

    # Remove consecutive duplicate lines
    cleaned = []
    for line in lines:
        if not cleaned or line != cleaned[-1]:
            cleaned.append(line)

    return "\n".join(cleaned)

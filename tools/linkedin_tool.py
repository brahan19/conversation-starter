"""
Custom CrewAI tool to fetch LinkedIn profile data via Proxycurl API.
"""
import os
from typing import Type

import requests
from pydantic import BaseModel, Field

from crewai.tools import BaseTool


class LinkedInToolInput(BaseModel):
    """Input schema for LinkedInTool."""

    linkedin_url: str = Field(
        ...,
        description="Full LinkedIn profile URL, e.g. https://www.linkedin.com/in/username/"
    )


class LinkedInTool(BaseTool):
    """Tool to scrape a LinkedIn profile using the Proxycurl API (nubela.co)."""

    name: str = "LinkedIn Profile Scraper"
    description: str = (
        "Fetches structured data for a LinkedIn profile given its URL. "
        "Use this to get the person's headline, experience, education, skills, "
        "and summary. Input must be the full LinkedIn profile URL."
    )
    args_schema: Type[BaseModel] = LinkedInToolInput

    def _run(self, linkedin_url: str) -> str:
        api_key = os.getenv("PROXYCURL_API_KEY")
        if not api_key:
            return (
                "LinkedIn API is not configured (PROXYCURL_API_KEY missing). "
                "Use web search (Firecrawl) instead: search for the person by name and profile URL "
                "to find their career, achievements, interests, articles, talks, and public presence. "
                "Extract the same kind of information you would from LinkedIn."
            )

        url = "https://nubela.co/proxycurl/api/v2/linkedin"
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"url": linkedin_url}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            # Return a readable summary for the agent (full JSON can be large)
            return self._format_profile(data)
        except requests.exceptions.RequestException as e:
            return f"Proxycurl API error: {e}"
        except Exception as e:
            return f"Error fetching LinkedIn profile: {e}"

    @staticmethod
    def _format_profile(data: dict) -> str:
        """Turn Proxycurl JSON into a concise text summary for agents."""
        parts = []

        if data.get("full_name"):
            parts.append(f"Name: {data['full_name']}")
        if data.get("headline"):
            parts.append(f"Headline: {data['headline']}")
        if data.get("summary"):
            parts.append(f"Summary: {data['summary']}")

        if data.get("experiences"):
            parts.append("\n## Experience")
            for exp in data["experiences"][:10]:
                title = exp.get("title", "N/A")
                company = exp.get("company", "N/A")
                start = exp.get("starts_at", {})
                end = exp.get("ends_at", {})
                start_str = f"{start.get('year', '')}-{start.get('month', '')}" if start else "?"
                end_str = f"{end.get('year', '')}-{end.get('month', '')}" if end else "Present"
                parts.append(f"- {title} at {company} ({start_str} to {end_str})")
                if exp.get("description"):
                    parts.append(f"  {exp['description'][:200]}...")

        if data.get("education"):
            parts.append("\n## Education")
            for edu in data["education"][:5]:
                school = edu.get("school", "N/A")
                degree = edu.get("degree_name") or edu.get("field_of_study") or ""
                parts.append(f"- {school} - {degree}")

        if data.get("skills"):
            parts.append("\n## Skills")
            skills = data["skills"][:20] if isinstance(data["skills"], list) else []
            parts.append(", ".join(skills) if skills else str(data["skills"]))

        if data.get("languages"):
            parts.append("\n## Languages")
            parts.append(", ".join(data["languages"]))

        if data.get("certifications"):
            parts.append("\n## Certifications")
            for cert in data["certifications"][:5]:
                parts.append(f"- {cert.get('name', cert)}")

        return "\n".join(parts) if parts else str(data)

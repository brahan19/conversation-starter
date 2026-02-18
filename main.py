"""
Networking research crew: hierarchical CrewAI crew that takes a LinkedIn URL
and produces pointed questions and conversation starters using research,
personal context, critique, and a question architect.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env not loaded if python-dotenv not installed

from crewai import Crew, Process, LLM
from agents import create_agents
from tasks import create_tasks

# Ensure required keys are present (at least for the LLM)
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY not set. Set it in .env for the crew to run.")


def run_crew(linkedin_url: str, name: str | None = None, current_work: str | None = None):
    """
    Run the hierarchical crew with the given LinkedIn profile URL and optional disambiguation inputs.
    name and current_work help disambiguate when many people share the same name.
    Returns the crew's output (final task result).
    """
    agents = create_agents()
    task_list = create_tasks(agents, linkedin_url, name=name, current_work=current_work)

    # Orchestrator is the manager; it must not be in the agents list (CrewAI requirement).
    worker_agents = [
        agents["web_researcher"],
        agents["personal_context_agent"],
        agents["evidence_filter_agent"],
        agents["review_critique_agent"],
        agents["question_architect"],
    ]

    cheap_llm = LLM(model="gpt-4o-mini")
    stronger_llm = LLM(model="gpt-4o")  # Better accuracy for research and report writing
    # Manager agent is not in crew.agents, so it does not get crew's default LLM; set it explicitly.
    agents["orchestrator"].llm = cheap_llm
    agents["web_researcher"].llm = stronger_llm
    agents["question_architect"].llm = stronger_llm
    crew = Crew(
        agents=worker_agents,
        tasks=task_list,
        process=Process.hierarchical,
        llm=cheap_llm,
        manager_agent=agents["orchestrator"],
        memory=True,
        verbose=True,
    )

    result = crew.kickoff()
    return result


if __name__ == "__main__":
    import argparse
    import re
    import sys
    from datetime import datetime

    parser = argparse.ArgumentParser(
        description="Run the Conversation Starter crew: research a LinkedIn profile and produce questions and conversation starters."
    )
    parser.add_argument(
        "linkedin_url",
        help="LinkedIn profile URL (e.g. https://www.linkedin.com/in/username/)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Person's full name (disambiguates when many people share the same name)",
    )
    parser.add_argument(
        "--current-work",
        dest="current_work",
        default=None,
        help="Person's current role/company (e.g. 'CTO at Acme Inc') for disambiguation",
    )
    args = parser.parse_args()

    url = args.linkedin_url.strip()
    name = args.name.strip() if args.name else None
    current_work = args.current_work.strip() if args.current_work else None

    print("Running crew for LinkedIn URL: {}".format(url))
    if name:
        print("  Name (disambiguation): {}".format(name))
    if current_work:
        print("  Current work (disambiguation): {}".format(current_work))
    print()
    output = run_crew(url, name=name, current_work=current_work)
    print("\n--- Crew output ---\n")
    result_str = str(output) if output is not None else ""
    print(result_str)

    # Save report in reports/ folder: {person_slug}_{timestamp}.md (prefer name-based slug when provided)
    slug_source = (name or url.strip("/").split("/")[-1] or "report").lower()
    person_slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug_source)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    report_filename = "{}_{}.md".format(person_slug, timestamp)
    report_path = os.path.join(report_dir, report_filename)
    if result_str.strip():
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(result_str)
        print("\nReport saved to {}".format(report_path))

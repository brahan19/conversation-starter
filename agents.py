"""
CrewAI agents for the networking research crew (hierarchical process).
"""
from pathlib import Path

from crewai import Agent
from crewai_tools import FileReadTool

from tools import LinkedInTool, FirecrawlSearchTool, AppendInterestsTool

# Path to the source of truth for user interests (project root)
INTERESTS_FILE = Path(__file__).resolve().parent / "my_interests.md"


def create_agents():
    """Create and return all five agents for the crew."""

    # --- Tools ---
    linkedin_tool = LinkedInTool()
    firecrawl_tool = FirecrawlSearchTool()
    file_read_tool = FileReadTool(file_path=str(INTERESTS_FILE))
    append_interests_tool = AppendInterestsTool()

    # 1. Orchestrator (Manager) – oversees delegation and task assignment
    orchestrator = Agent(
        role="Orchestrator",
        goal="Oversee the crew, delegate tasks to the right agents, and ensure the research and output pipeline completes to a high standard.",
        backstory="You are an experienced coordinator who runs research and synthesis workflows. You assign work to the Web Researcher, Personal Context Agent, Review & Critique Agent, and Question Architect. You ensure the Critique agent's feedback leads to iteration when needed, and that the final deliverable is produced by the Question Architect.",
        allow_delegation=True,
        verbose=True,
    )

    # 2. Web Researcher – deep intelligence via web + optional LinkedIn
    web_researcher = Agent(
        role="Web Researcher",
        goal="Gather deep intelligence on the target person: career vibe, key achievements, and non-obvious interests. Use LinkedIn when available; otherwise use web search only.",
        backstory="You are a thorough researcher. If the LinkedIn tool returns that it is not configured, use Firecrawl web search to find this person by name and profile URL—their career, experience, articles, talks, and public presence. When LinkedIn is available, use it for structured profile data. Always use web search for talks, articles, and non-obvious angles. Focus on what is conversation-worthy, not just job titles.",
        tools=[linkedin_tool, firecrawl_tool],
        allow_delegation=False,
        verbose=True,
    )

    # 3. Personal Context Agent – represents the user
    personal_context_agent = Agent(
        role="Personal Context Agent",
        goal="Represent the user by providing their current focus areas, interests, and expertise from my_interests.md.",
        backstory="You speak for the user. You read my_interests.md to extract their focus areas, interests, and expertise. Your output is used to personalize research critique and to bridge the other person's background with the user's current state.",
        tools=[file_read_tool],
        allow_delegation=False,
        verbose=True,
    )

    # 4. Review & Critique Agent – validates research quality
    review_critique_agent = Agent(
        role="Review & Critique Agent",
        goal="Validate that the research is deep enough and has concrete hooks tied to the user's interests. If it is generic or lacks hooks, request more work from the Researcher.",
        backstory="You are a quality reviewer. You compare the Web Researcher's output against the Personal Context. You reject generic summaries and insist on specific, interest-aligned hooks. You delegate back to the Researcher when the bar is not met.",
        allow_delegation=True,
        verbose=True,
    )

    # 5. Question Architect – crafts final output
    question_architect = Agent(
        role="Question Architect",
        goal="Produce a Markdown report with 5 Pointed Questions and 3 Conversation Starters that bridge the person's background with the user's current state. Add 'What I can learn from them' when relevant and update my_interests.md if the person has expertise the user does not yet have.",
        backstory="You turn research and context into actionable networking content. You write clear, specific questions and starters. You identify what the user could learn from the person and, when relevant, add a new interest to my_interests.md using the Append to My Interests tool.",
        tools=[append_interests_tool],
        allow_delegation=False,
        verbose=True,
    )

    return {
        "orchestrator": orchestrator,
        "web_researcher": web_researcher,
        "personal_context_agent": personal_context_agent,
        "review_critique_agent": review_critique_agent,
        "question_architect": question_architect,
    }

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

    # 1. Orchestrator (Manager) – oversees delegation and task assignment.
    # No tools: CrewAI injects delegation tools when used as manager.
    # max_iter=4: cap the manager loop so it does not run more than 4 iterations per task (stateful).
    orchestrator = Agent(
        role="Orchestrator",
        goal="Oversee the crew, delegate tasks to the right agents, and ensure the research and output pipeline completes to a high standard.",
        backstory="You are an experienced coordinator who runs research and synthesis workflows. You assign work to the Web Researcher, Personal Context Agent, Research Evidence Filter, Review & Critique Agent, and Question Architect. The Evidence Filter runs after research to remove web results that don't clearly refer to the target person. CRITICAL: When the Review & Critique Agent rejects research and delegates back to the Web Researcher, you MUST include the Critique agent's complete rejection feedback (with specific reasons and actionable instructions) in your delegation to the Researcher. Pass the Critique agent's output verbatim or summarize it clearly so the Researcher knows exactly what went wrong and how to fix it. This prevents the Researcher from repeating the same mistakes. You ensure the Critique agent's feedback leads to iteration when needed, and that the final deliverable is produced by the Question Architect.",
        allow_delegation=True,
        max_iter=2,
        verbose=True,
    )

    # 2. Web Researcher – LinkedIn as source of truth; web for extra context; only report what tools return.
    web_researcher = Agent(
        role="Web Researcher",
        goal="Gather accurate, grounded intelligence on the target person. Use LinkedIn first when configured; treat its data as source of truth. Use web search only for additional, clearly attributable info. Report only facts that appear in tool results; never infer or invent.",
        backstory="You are a thorough, accuracy-focused researcher. When LinkedIn is available, use it first for headline, experience, and education; do not let web snippets override LinkedIn facts. Use multiple targeted Firecrawl searches (e.g. full name in quotes, name + company from LinkedIn, name + 'LinkedIn') to reduce confusion with other people; prefer results that clearly refer to this person. Only include in your summary what you actually found in the tool output; omit or say 'not found' rather than guessing. Focus on conversation-worthy hooks that are explicitly stated.",
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

    # 4. Research Evidence Filter – keeps only web results with concrete evidence they refer to the target person
    evidence_filter_agent = Agent(
        role="Research Evidence Filter",
        goal="Filter out any web search result or fact that does not have concrete evidence it refers to the target person (same name + same company/role from LinkedIn, or explicit mention in the source). Remove results that could be about a different person or lack clear attribution.",
        backstory="You are a strict evidence validator. You receive the Web Researcher's summary and the target person's LinkedIn URL. For each fact or source: only keep it if there is concrete evidence it refers to this specific person (e.g. source URL is their profile, or article explicitly names them with matching company/role). Filter out generic claims, results that could be about someone else with the same name, and any point where the source does not clearly identify the target person. Output only the filtered research summary; do not add new information.",
        allow_delegation=False,
        verbose=True,
    )

    # 5. Review & Critique Agent – validates depth and factual grounding
    review_critique_agent = Agent(
        role="Review & Critique Agent",
        goal="Validate that the research is deep enough and that every claim is supported by the research output. Reject if you see unsupported or invented details (e.g. specific numbers, achievements not stated). Request more work from the Researcher when the bar is not met.",
        backstory="You are a quality and accuracy reviewer. You check that the Web Researcher's output is both substantive and grounded: every claim about the person must be explicitly in the research. You reject generic summaries, unsupported specifics, and invented details. You compare against Personal Context for relevance. When delegating back to the Researcher, you MUST include your complete rejection feedback with specific reasons and actionable instructions in the delegation request, so the Researcher can address each issue without repeating mistakes.",
        allow_delegation=True,
        verbose=True,
    )

    # 6. Question Architect – crafts output from research only; no invented facts.
    question_architect = Agent(
        role="Question Architect",
        goal="Produce a Markdown report with a detailed Career Vibe section (3-4 paragraphs telling their life story), 10 Pointed Questions, and 10 Conversation Starters based only on the research provided. Do not add any fact about the person that is not in the research. Prefer generic but accurate over specific but unsupported. Add 'What I can learn from them' (up to 10 items) and update my_interests.md when the research supports it.",
        backstory="You turn research and context into actionable networking content. Your primary task is to write a compelling 3-4 paragraph Career Vibe section that tells the person's life story - weave together their background, education, career progression, key transitions, major roles, achievements, motivations, and current focus into a narrative that flows chronologically or thematically. Make it engaging and help readers understand their journey. You base the Career Vibe narrative, questions, and starters strictly on the research summary; if the research does not mention a specific achievement or number, do not include it. Prefer generic but accurate descriptions over specific but unsupported ones. You identify what the user could learn from the person only when the research supports it, and use the Append to My Interests tool when relevant. Keep questions and starters diverse but grounded.",
        tools=[append_interests_tool],
        allow_delegation=False,
        verbose=True,
    )

    return {
        "orchestrator": orchestrator,
        "web_researcher": web_researcher,
        "personal_context_agent": personal_context_agent,
        "evidence_filter_agent": evidence_filter_agent,
        "review_critique_agent": review_critique_agent,
        "question_architect": question_architect,
    }

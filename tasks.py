"""
CrewAI tasks for the networking research crew (hierarchical process).
"""
from crewai import Task, Agent


def create_tasks(agents: dict, linkedin_url: str):
    """
    Create the four tasks. Pass the linkedin_url so the Research task can use it.
    """
    web_researcher = agents["web_researcher"]
    personal_context_agent = agents["personal_context_agent"]
    review_critique_agent = agents["review_critique_agent"]
    question_architect = agents["question_architect"]

    # 1. Research Task – LinkedIn (optional) + web search for career vibe, achievements, non-obvious interests
    research_task = Task(
        description=(
            "Produce a summary of this person's career 'vibe,' key achievements, and non-obvious interests. "
            "Optionally use the LinkedIn tool with this URL: {linkedin_url} — if it says it is not configured, "
            "use only web search. Always use web search (Firecrawl) to find them by name/URL: talks, articles, "
            "side projects, and public presence. Focus on what would make for good conversation hooks, not just job titles."
        ).format(linkedin_url=linkedin_url),
        expected_output=(
            "A structured summary: (1) Career vibe in 2–3 sentences, "
            "(2) Key achievements (bullets), (3) Non-obvious interests or angles (bullets)."
        ),
        agent=web_researcher,
    )

    # 2. Context Sync Task – Extract my focus areas from my_interests.md
    context_sync_task = Task(
        description=(
            "Read my_interests.md and extract the user's current focus areas, interests, and expertise. "
            "Provide a concise summary that can be used to validate research quality and to craft "
            "personalized questions and conversation starters."
        ),
        expected_output=(
            "A short summary of: current focus areas, interests list, and expertise. "
            "Keep it scannable so the Critique and Question Architect can use it."
        ),
        agent=personal_context_agent,
    )

    # 3. Critique Task – Evaluate research depth; allow_delegation so manager can send back to Researcher
    # Prefer to approve when research has substantive content to avoid repeated iterations when testing.
    critique_task = Task(
        description=(
            "Evaluate whether the research produced by the Web Researcher is deep enough. "
            "Compare it against the Personal Context (user's interests and focus). "
            "Prefer to approve if the research has any substantive content (career vibe, achievements, or interests). "
            "Only delegate back to the Web Researcher if the research is clearly generic, empty, or lacks any concrete hooks. "
            "If it meets the bar or is reasonably usable, approve it for the Question Architect."
        ),
        expected_output=(
            "Either: (a) Approval with a one-sentence handoff to the Question Architect, or "
            "(b) Rejection with specific instructions for the Web Researcher to improve the research."
        ),
        agent=review_critique_agent,
        context=[research_task, context_sync_task],
        allow_delegation=True,
    )

    # 4. Output Task – Markdown report + optional "What I can learn" and my_interests.md update
    output_task = Task(
        description=(
            "Produce a Markdown report for the user with: "
            "(1) A brief recap of the person's career vibe and key points. "
            "(2) Five Pointed Questions – specific questions that bridge their background with the user's current state. "
            "(3) Three Conversation Starters – openers that connect their experience to the user's interests. "
            "Final logic: If the person has an expertise or area the user does not yet have, "
            "append a 'What I can learn from them' section to the report AND, if relevant, "
            "use the 'Append to My Interests' tool to add a new Interest entry to my_interests.md."
        ),
        expected_output=(
            "A Markdown report containing: recap, 5 Pointed Questions, 3 Conversation Starters, "
            "and optionally 'What I can learn from them' and an updated my_interests.md (via the tool)."
        ),
        agent=question_architect,
        context=[research_task, context_sync_task, critique_task],
    )

    return [research_task, context_sync_task, critique_task, output_task]

"""
CrewAI tasks for the networking research crew (hierarchical process).
"""
from crewai import Task, Agent


def create_tasks(
    agents: dict,
    linkedin_url: str,
    name: str | None = None,
    current_work: str | None = None,
):
    """
    Create the five tasks. Pass linkedin_url for Research and Evidence Filter.
    name and current_work are used to disambiguate when many people share the same name.
    """
    web_researcher = agents["web_researcher"]
    personal_context_agent = agents["personal_context_agent"]
    evidence_filter_agent = agents["evidence_filter_agent"]
    review_critique_agent = agents["review_critique_agent"]
    question_architect = agents["question_architect"]

    # Disambiguation context for tasks (avoid mixing into prompts when not provided)
    name_ctx = name.strip() if name else ""
    current_work_ctx = current_work.strip() if current_work else ""
    disambiguation_note = ""
    if name_ctx and current_work_ctx:
        disambiguation_note = (
            " The target person's name is \"{name}\" and their current work (company/role) is \"{current_work}\". "
            "Use these to disambiguate: e.g. search for both name and current work so results refer to this person, not someone else with the same name."
        ).format(name=name_ctx, current_work=current_work_ctx)
    elif name_ctx:
        disambiguation_note = (
            " The target person's name is \"{name}\". Use it to disambiguate web search so results refer to this person."
        ).format(name=name_ctx)
    elif current_work_ctx:
        disambiguation_note = (
            " The target person's current work (company/role) is \"{current_work}\". Use it to disambiguate web search."
        ).format(current_work=current_work_ctx)

    # 1. Research Task – LinkedIn as source of truth when available; web for extra context. Ground all facts.
    research_task = Task(
        description=(
            "Produce a summary of this person's career vibe, key achievements, and non-obvious interests. "
            "When the LinkedIn tool is configured, use it first with this URL: {linkedin_url}. Treat LinkedIn data "
            "(headline, experience, education) as the source of truth for job titles, companies, and dates. "
            "Use web search (Firecrawl) only to add additional information (talks, articles, side projects) that "
            "clearly refers to this person; do not let web snippets contradict or replace LinkedIn facts. "
            "If LinkedIn is not configured, use only web search.{disambiguation}\n\n"
            "CRITICAL: Only include facts that appear in the tool results. Do not infer, assume, or invent any "
            "details (e.g. numbers, titles, achievements). If a claim is not clearly stated in the tool output, omit it. "
            "Prefer saying 'not found' over guessing. Focus on conversation-worthy hooks that are explicitly supported.\n\n"
            "If you receive feedback from the Review & Critique Agent (in your context), carefully review their "
            "rejection reasons and specific instructions. Address each issue they identified: fix unsupported claims, "
            "add missing sources, search for more concrete information, or remove generic content as directed. "
            "Do not repeat the same mistakes that led to the rejection."
        ).format(linkedin_url=linkedin_url, disambiguation=disambiguation_note),
        expected_output=(
            "A structured summary: (1) Career vibe with enough detail for a narrative (include career progression, "
            "key transitions, motivations, and notable experiences), (2) Key achievements (bullets), "
            "(3) Non-obvious interests or angles (bullets). For each fact from web search, include the source URL "
            "(e.g. 'Source: https://...') so the Evidence Filter can verify the result refers to this person. "
            "Every bullet must be traceable to a specific tool result; do not add unsupported claims. "
            "Gather enough information about their career journey, education, major roles, transitions, and motivations "
            "to enable writing a compelling 3-4 paragraph life story. If this is a revision based on critique feedback, "
            "explicitly address the issues raised in the feedback."
        ),
        agent=web_researcher,
    )

    # 2. Evidence Filter Task – Keep only research with concrete evidence it refers to the target person
    filter_disambiguation = ""
    if name_ctx and current_work_ctx:
        filter_disambiguation = (
            " The target person's name is \"{name}\" and current work is \"{current_work}\". "
            "Only keep results that clearly refer to this person (matching name and preferably current work/company); "
            "remove results that could be about a different person with the same name."
        ).format(name=name_ctx, current_work=current_work_ctx)
    elif name_ctx:
        filter_disambiguation = (
            " The target person's name is \"{name}\". Only keep results that clearly refer to this person, not someone else with the same name."
        ).format(name=name_ctx)
    elif current_work_ctx:
        filter_disambiguation = (
            " The target person's current work is \"{current_work}\". Use it to verify results refer to this person."
        ).format(current_work=current_work_ctx)

    filter_task = Task(
        description=(
            "You receive the Web Researcher's summary and the target person's LinkedIn URL: {linkedin_url}.{filter_disc}"
            " Filter out any fact or web search result that does NOT have concrete evidence it refers to this specific person. "
            "Keep only: (1) Facts from LinkedIn (they refer to this profile). "
            "(2) Web results where the source explicitly names the person AND matches their company/role (e.g. same company as LinkedIn), "
            "or the URL clearly identifies them (e.g. their blog, their talk, their company profile naming them). "
            "Remove: generic claims, results that could be about another person with the same name, any fact whose source "
            "does not clearly identify the target person. Output a filtered research summary with only the facts that pass; "
            "do not add new information. If in doubt, exclude the fact."
        ).format(linkedin_url=linkedin_url, filter_disc=filter_disambiguation),
        expected_output=(
            "A filtered research summary with the same structure (career vibe, key achievements, interests) but containing "
            "only facts that have concrete evidence they refer to the target person. List which items were removed and why "
            "(one line each), then the filtered summary."
        ),
        agent=evidence_filter_agent,
        context=[research_task],
    )

    # 3. Context Sync Task – Extract my focus areas from my_interests.md
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

    # 4. Critique Task – Check depth and factual grounding of the filtered research.
    critique_task = Task(
        description=(
            "Evaluate the FILTERED research (output of the Research Evidence Filter) on two dimensions: "
            "(1) Depth and relevance to the user's interests (Personal Context). "
            "(2) Factual accuracy: every claim about the person must be explicitly supported by the filtered research. "
            "Reject if you see specific claims (e.g. exact figures) not stated in the filtered research. "
            "Prefer approving only when the filtered summary is both substantive and grounded. "
            "Delegate back to the Web Researcher if the filtered research is generic, empty, lacks concrete hooks, or "
            "contains unsupported details. If it meets the bar, approve for the Question Architect."
        ),
        expected_output=(
            "Either: (a) Approval with a one-sentence handoff to the Question Architect, or "
            "(b) Rejection with CLEAR, ACTIONABLE feedback for the Web Researcher. When rejecting, you MUST include: "
            "(1) Specific reasons for rejection (e.g. 'Claim X lacks source', 'Too generic - missing concrete achievements', "
            "'Unsupported detail Y was included'), (2) Concrete instructions on what to fix (e.g. 'Search for specific projects', "
            "'Include source URLs for all claims', 'Remove unsupported achievement Z'). This feedback will be passed to the "
            "Web Researcher so they can address the issues without repeating the same mistakes."
        ),
        agent=review_critique_agent,
        context=[filter_task, context_sync_task],
        allow_delegation=True,
    )

    # 5. Output Task – Markdown report grounded in filtered research only; no invented facts.
    output_task = Task(
        description=(
            "Produce a Markdown report for the user with: "
            "(1) A detailed Career Vibe section (3-4 paragraphs) that tells the person's life story. Write this as a "
            "narrative that flows chronologically or thematically, covering: their background/education, career progression "
            "and key transitions, major roles and achievements, what drives them, and their current focus. Make it engaging "
            "and help the reader understand their journey and motivations. Use transitions between paragraphs to create a "
            "cohesive story. Base this entirely on the FILTERED research summary - weave together the facts into a narrative, "
            "but do not invent or infer details not present in the research. "
            "(2) Key Points section with bullet points highlighting major achievements and roles. "
            "(3) Ten Pointed Questions – specific questions that bridge their background with the user's current state. "
            "(4) Ten Conversation Starters – openers that connect their experience to the user's interests. "
            "CRITICAL: Base the Career Vibe narrative and all questions/starters only on the FILTERED research summary provided "
            "(the output of the Research Evidence Filter). Do not add any fact about the person that is not in that "
            "filtered research. If the research is sparse, keep the narrative conservative and generic rather than inventing details. "
            "Prefer generic but accurate descriptions over specific but unsupported ones. "
            "If the person has an expertise or area the user does not yet have, append 'What I can learn from them' "
            "with up to ten items and, if relevant, use the 'Append to My Interests' tool to add a new Interest entry to my_interests.md."
        ),
        expected_output=(
            "A Markdown report containing: a detailed Career Vibe section (3-4 paragraphs telling their life story), "
            "Key Points (bullets), 10 Pointed Questions, 10 Conversation Starters, "
            "and optionally 'What I can learn from them' (up to 10 items) and an updated my_interests.md (via the tool). "
            "Every claim about the person in the Career Vibe narrative must appear in the filtered research; no unsupported details."
        ),
        agent=question_architect,
        context=[filter_task, context_sync_task, critique_task],
    )

    return [research_task, context_sync_task, filter_task, critique_task, output_task]

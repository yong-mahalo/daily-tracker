import json

import anthropic

from app.config import ANTHROPIC_API_KEY
from app.services import goals as goal_repo


def _build_system_prompt(goals: list[dict]) -> str:
    """Construct the LLM system prompt from the user's configured goals."""
    if not goals:
        raise ValueError(
            "No goals configured. Visit /settings to create at least one goal."
        )

    goal_lines = []
    for i, g in enumerate(goals, start=1):
        desc = f" — {g['description']}" if g.get("description") else ""
        goal_lines.append(f'  {i}. {g["label"]} (goal key: "{g["key"]}"){desc}')

    goal_keys = "|".join(g["key"] for g in goals)
    summaries_template = ",\n    ".join(
        f'"{g["key"]}": "<1-2 sentence summary of {g["label"]} activity, or null if none>"'
        for g in goals
    )

    return f"""You are a personal productivity assistant. The user is actively tracking progress across these parallel goals:

{chr(10).join(goal_lines)}

When given a free-form brain dump, extract every distinct action, task, or progress update. Assign each item to exactly one goal.
Items not related to any of the goals (e.g. personal errands, general study) are noted in "general_notes" only and NOT included in the tasks array.

Valid category values: "application", "outreach", "research", "networking", "profile", "learning", "admin", "general"
Valid status values: "done", "in_progress", "logged"
  - "done": completed today
  - "in_progress": started but not finished
  - "logged": noted as a to-do or intention

Respond ONLY with valid JSON matching this exact schema. No prose before or after the JSON object.

{{
  "tasks": [
    {{
      "goal": "<{goal_keys}>",
      "task_text": "<concise description of the task>",
      "category": "<category>",
      "effort_minutes": <integer or null>,
      "status": "<done|in_progress|logged>"
    }}
  ],
  "summaries": {{
    {summaries_template}
  }},
  "general_notes": "<any non-goal activity briefly noted, or null>"
}}"""


def parse_brain_dump(raw_text: str, entry_date: str, model: str) -> tuple[dict, int]:
    """
    Send raw text to Claude. Returns (parsed_dict, total_tokens).
    Raises on API error or JSON parse failure.
    """
    goals = goal_repo.list_goals()
    system_prompt = _build_system_prompt(goals)
    valid_keys = {g["key"] for g in goals}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Date: {entry_date}\nBrain dump:\n---\n{raw_text}\n---\n\nExtract tasks and produce the JSON response.",
            }
        ],
    )

    raw_response = message.content[0].text
    tokens = message.usage.input_tokens + message.usage.output_tokens

    parsed = json.loads(raw_response)
    _validate(parsed, valid_keys)
    return parsed, tokens


def _validate(parsed: dict, valid_keys: set[str]) -> None:
    if "tasks" not in parsed:
        raise ValueError("Missing 'tasks' key in LLM response")
    if "summaries" not in parsed:
        raise ValueError("Missing 'summaries' key in LLM response")
    for task in parsed["tasks"]:
        if task.get("goal") not in valid_keys:
            raise ValueError(f"Invalid goal value: {task.get('goal')}")

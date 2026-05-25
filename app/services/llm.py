import json

import anthropic

from app.config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """You are a personal productivity assistant for Yonghao, a researcher actively pursuing three parallel career tracks:
  1. PhD positions (goal key: "phd") — academic positions in HCI, accessibility, AI for education, participatory design, co-design, XR, LLMs.
  2. Netherlands jobs (goal key: "nl_jobs") — industry or research roles in the Netherlands; includes learning Dutch.
  3. China jobs (goal key: "china_jobs") — roles in China (industry or academic), especially during spring recruitment season.

When given a free-form brain dump, extract every distinct action, task, or progress update. Assign each item to exactly one goal.
Items not related to any of the three goals (e.g., personal errands, general study) are noted in "general_notes" only and NOT included in the tasks array.

Valid category values: "application", "outreach", "research", "networking", "profile", "learning", "admin", "general"
Valid status values: "done", "in_progress", "logged"
  - "done": completed today
  - "in_progress": started but not finished
  - "logged": noted as a to-do or intention

Respond ONLY with valid JSON matching this exact schema. No prose before or after the JSON object.

{
  "tasks": [
    {
      "goal": "<phd|nl_jobs|china_jobs>",
      "task_text": "<concise description of the task>",
      "category": "<category>",
      "effort_minutes": <integer or null>,
      "status": "<done|in_progress|logged>"
    }
  ],
  "summaries": {
    "phd": "<1-2 sentence summary of PhD-related activity, or null if none>",
    "nl_jobs": "<1-2 sentence summary of NL job activity, or null if none>",
    "china_jobs": "<1-2 sentence summary of China job activity, or null if none>"
  },
  "general_notes": "<any non-goal activity briefly noted, or null>"
}"""


def parse_brain_dump(raw_text: str, entry_date: str, model: str) -> tuple[dict, int]:
    """
    Send raw text to Claude. Returns (parsed_dict, total_tokens).
    Raises on API error or JSON parse failure.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0,
        system=SYSTEM_PROMPT,
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
    _validate(parsed)
    return parsed, tokens


def _validate(parsed: dict) -> None:
    """Raise ValueError if the parsed dict is missing required keys."""
    if "tasks" not in parsed:
        raise ValueError("Missing 'tasks' key in LLM response")
    if "summaries" not in parsed:
        raise ValueError("Missing 'summaries' key in LLM response")
    valid_goals = {"phd", "nl_jobs", "china_jobs"}
    for task in parsed["tasks"]:
        if task.get("goal") not in valid_goals:
            raise ValueError(f"Invalid goal value: {task.get('goal')}")

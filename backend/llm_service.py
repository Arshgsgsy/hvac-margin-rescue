import anthropic
from config import ANTHROPIC_API_KEY
from prompts import SYSTEM_PROMPT, build_project_context, root_cause_prompt


def stream_chat(project: dict, question: str):
    """Generator that yields text chunks from Claude for a project chat."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    context = build_project_context(project)
    prompt = root_cause_prompt(context, question)

    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text

"""Generate answers to job application questions using AI."""

import json
from utils import run_claude


def generate_answer(
    question: str,
    job_title: str,
    company: str,
    job_description: str,
    user_background: str
) -> str:
    """Generate an answer to a job application question using Claude.

    Args:
        question: The application question to answer
        job_title: The job title
        company: Company name
        job_description: Full job description (can be empty)
        user_background: User's combined source documents or comprehensive summary

    Returns:
        Generated answer text, or empty string on failure
    """
    if not question or not user_background:
        return ""

    job_context = ""
    if job_description:
        job_context = f"""
JOB CONTEXT:
Company: {company}
Position: {job_title}
Description:
{job_description}
"""

    prompt = f"""Answer this job application question based on the candidate's background.

CANDIDATE BACKGROUND:
{user_background}
{job_context}
QUESTION:
{question}

INSTRUCTIONS:
- Write a clear, specific answer tailored to the candidate's actual experience
- Include concrete examples, metrics, and details from their background where relevant
- Keep it concise but substantive (typically 50-200 words depending on the question)
- If the question asks for a list or specific items, format appropriately
- Match the tone to the question type (technical questions get technical answers,
  motivational questions can be more personal)
- If the background doesn't contain relevant information, write a reasonable answer
  based on what is provided, but don't fabricate specific details

WRITING STYLE:
- Use first person (I, my, we)
- Be direct and specific
- Avoid generic phrases like "I am passionate about" or "I am excited to"
- Don't over-explain or pad the answer
- Use contractions for natural tone (I've, I'm, wasn't)

Write the answer now:"""

    success, response = run_claude(prompt, timeout=90)

    if not success:
        return ""

    return response.strip()


def generate_answers_batch(
    questions: list[str],
    job_title: str,
    company: str,
    job_description: str,
    user_background: str
) -> list[dict]:
    """Generate answers for multiple questions at once.

    Args:
        questions: List of question strings
        job_title: The job title
        company: Company name
        job_description: Full job description
        user_background: User's combined source documents

    Returns:
        List of dicts with "question" and "answer" keys
    """
    if not questions or not user_background:
        return []

    job_context = ""
    if job_description:
        job_context = f"""
JOB CONTEXT:
Company: {company}
Position: {job_title}
Description:
{job_description}
"""

    questions_formatted = "\n".join(
        f"{i+1}. {q}" for i, q in enumerate(questions)
    )

    prompt = f"""Answer these job application questions based on the candidate's background.

CANDIDATE BACKGROUND:
{user_background}
{job_context}
QUESTIONS:
{questions_formatted}

INSTRUCTIONS:
- Write clear, specific answers tailored to the candidate's actual experience
- Include concrete examples, metrics, and details from their background where relevant
- Keep answers concise but substantive (typically 50-200 words each)
- Match the tone to each question type
- Use first person (I, my)
- Be direct and specific, avoid generic phrases

OUTPUT FORMAT:
Return ONLY a JSON array with objects for each question. Each object must have:
- "question": The original question text
- "answer": Your generated answer

Example:
[
    {{"question": "Why do you want to work here?", "answer": "Your focus on climate tech aligns with my research background..."}},
    {{"question": "What's your experience with Python?", "answer": "I've used Python for 6 years, primarily for data analysis..."}}
]

Return ONLY the JSON array, no other text:"""

    success, response = run_claude(prompt, timeout=180)

    if not success:
        return []

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

        results = json.loads(cleaned)
        if isinstance(results, list):
            return results
    except json.JSONDecodeError:
        pass

    return []

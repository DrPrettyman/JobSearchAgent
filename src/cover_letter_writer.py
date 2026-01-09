"""
Generate PDF cover letters from using LaTeX.
"""

import json
import subprocess
import tempfile
import re
from datetime import datetime, timezone
from pathlib import Path

from utils import run_claude

LATEX_TEMPLATE = r"""\documentclass[11pt]{article}

\usepackage[paper=a4paper,
            margin=25mm]{geometry}

\usepackage{hyperref}
\usepackage{color}
\definecolor{darkblue}{rgb}{0.0,0.0,0.3}
\hypersetup{colorlinks,breaklinks,
            linkcolor=darkblue,urlcolor=darkblue,
            anchorcolor=darkblue,citecolor=darkblue}

\setlength{\parindent}{0pt}
\setlength{\parskip}{12pt}

\pagestyle{empty}

\begin{document}

% Letterhead
\begin{center}
{\Large \underline{<INSERT_USER_NAME>}}

\vspace{4pt}

<INSERT_CONTACT_INFO>
\end{center}

\vspace{20pt}

<INSERT_DATE>

\vspace{12pt}

% Subject line
\textbf{RE: <INSERT_TITLE> role at <INSERT_COMPANY>}

\vspace{12pt}

% Salutation
Dear <INSERT_ADDRESSEE>,

% Body
<INSERT_BODY>

\vspace{12pt}

Yours <INSERT_SIGNOFF>,

\vspace{24pt}

Joshua Prettyman

\end{document}
"""


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in text."""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def compile_latex_to_pdf(latex_source: str, output_path: Path) -> bool:
    """Compile LaTeX source to PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = Path(tmpdir) / "latex_source.tex"
        tex_file.write_text(latex_source)

        # Run pdflatex twice for references
        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_file)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"LaTeX compilation error:\n{result.stdout}\n{result.stderr}")
                return False

        # Copy PDF to output location
        pdf_file = Path(tmpdir) / "latex_source.pdf"
        if pdf_file.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(pdf_file.read_bytes())
            return True
        return False


class LetterWriter:
    def __init__(self, 
        company: str,
        title: str,
        cover_letter_body: str,
        user_name: str,
        user_email: str,
        user_linkedin_ext: str,
        user_credentials: list[str] = None,
        user_website: str = None,
        addressee: str = None):
        
        self.company: str = company
        self.title: str = title
        self.cover_letter_body: str = cover_letter_body
        
        self.user_name = user_name
        self.user_credentials = user_credentials  # e.g. ["PhD", "MBA"]
        self.user_email = user_email
        self.user_linkedin_ext = user_linkedin_ext
        self.user_website = user_website
        
        if addressee:
            self.addressee = addressee
            self.sign_off: str = "sincerely"
        else:           
            self.addressee = "hiring team"
            self.sign_off = "faithfully"
            
        self.filename: str = self.make_filename()
    
    def make_filename(self) -> str:
        """Convert company name to safe filename."""
        name = re.sub(r"\W+", "", self.user_name)
        sanitized = self.company.replace(' ', '_').replace('/', '_').replace('\\', '_')
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"{sanitized}_{name}_CoverLetter_{timestamp}"
    
    @property
    def contact_info(self) -> str:
        email = r"\href{mailto:email}{email}".replace("email", self.user_email)
        linkedin = r"\href{https://linkedin.com/in/ext}{in/ext}".replace("ext", self.user_linkedin_ext)

        if self.user_website:
            website = r"\href{<FULL>}{<STRIPPED>}".replace("<FULL>", self.user_website).replace("<STRIPPED>", re.sub(r"https?://", "", self.user_website))
            contact_info = [email, website, linkedin]
        else:
            contact_info = [email, linkedin]

        return r" \textbar{} ".join(contact_info)
            
    @property
    def full_name_for_header(self) -> str:
        if self.user_credentials:
            return ", ".join([self.user_name] + self.user_credentials)
        else:
            return self.user_name
        
    @property
    def latex_source_cover_letter(self) -> str:
        """Generate LaTeX source for a cover letter."""
        
        # Escape text for LaTeX (but not contact_info which contains LaTeX commands)
        user_name_escaped = escape_latex(self.full_name_for_header)
        company_escaped = escape_latex(self.company)
        cover_letter_escaped = escape_latex(self.cover_letter_body)
        title_escaped = escape_latex(self.title)
        addressee_escaped = escape_latex(self.addressee)

        # Format current date
        current_date = datetime.now().strftime("%d %B %Y")

        # Convert newlines to LaTeX paragraph breaks
        cover_letter_formatted = cover_letter_escaped.replace('\n', '\n\n')

        latex_template = LATEX_TEMPLATE
        latex_template = latex_template.replace('<INSERT_USER_NAME>', user_name_escaped.upper())
        latex_template = latex_template.replace('<INSERT_CONTACT_INFO>', self.contact_info)
        latex_template = latex_template.replace('<INSERT_DATE>', current_date)
        latex_template = latex_template.replace('<INSERT_TITLE>', title_escaped)
        latex_template = latex_template.replace('<INSERT_COMPANY>', company_escaped)
        latex_template = latex_template.replace('<INSERT_ADDRESSEE>', addressee_escaped)
        latex_template = latex_template.replace('<INSERT_BODY>', cover_letter_formatted)
        latex_template = latex_template.replace('<INSERT_SIGNOFF>', self.sign_off)

        return latex_template      

    def save_pdf(self, output_dir: Path) -> Path | None:
        """Save PDF cover letter to file."""
        output_path = output_dir / f"{self.filename}.pdf"
        compiled = compile_latex_to_pdf(self.latex_source_cover_letter, output_path)
        if compiled:
            return output_path
        else:
            return None


def generate_cover_letter_topics(
    job_description: str,
    user_background: str
) -> list[dict]:
    """Analyze job description and generate cover letter topics.

    Follows Steps 1-3 from claude-instructions.md:
    1. Analyse the job description for key topics
    2. Map each topic to relevant candidate experience
    3. Select 3-5 strongest points

    Args:
        job_description: Full job description
        user_background: User's combined source documents

    Returns:
        List of dicts with "topic" and "relevant_experience" keys, or empty list on failure
    """
    if not job_description or not user_background:
        return []

    prompt = f"""Analyze this job description and candidate background to identify cover letter topics.

JOB DESCRIPTION:
{job_description}

CANDIDATE BACKGROUND:
{user_background}

STEP 1: Analyze the job description carefully. Look for topics across:
- Company description and mission
- Sector/industry
- Team composition and culture
- Role responsibilities
- Required skills
- Nice-to-haves
- Any specific phrases or values mentioned

STEP 2: For each topic you identify, map it to the candidate's relevant experience.

Don't just list "Required Skills" verbatim. Also look for:
- Implicit requirements (e.g., "team of PhDs" implies academic background matters)
- Company values or mission statements
- Industry-specific context
- Team structure clues

STEP 3: Select the 3-5 strongest topics where the candidate has the most specific, concrete experience. Prioritize:
- Topics where concrete metrics or outcomes can be cited
- Topics that differentiate this candidate from others
- Topics the company emphasizes most (mentioned multiple times, in headlines, etc.)

OUTPUT FORMAT:
Return ONLY a JSON array with 3-5 objects. Each object must have:
- "topic": The job requirement or theme (quote key phrases from the job description)
- "relevant_experience": Specific experience the candidate has (include metrics where possible)

Example:
[
    {{"topic": "Proficiency in Python ecosystem (Pandas, Matplotlib, Scikit-Learn); deploying end-to-end ML models", "relevant_experience": "Built full ML platform at Blink processing 50M+ data points daily; NLP clustering, embeddings, sklearn"}},
    {{"topic": "sustainability sector", "relevant_experience": "MRes and PhD part of Mathematics of Planet Earth programme; PhD focused on tipping point detection in climate systems"}}
]

Return ONLY the JSON array, no other text:"""

    success, response = run_claude(prompt, timeout=120)

    if not success:
        return []

    # Parse JSON response
    try:
        # Clean up response - remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]  # Remove first line
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()

        topics = json.loads(cleaned)
        if isinstance(topics, list):
            return topics
    except json.JSONDecodeError:
        pass

    return []


def generate_cover_letter_body(
    job_title: str,
    company: str,
    job_description: str,
    user_background: str,
    cover_letter_topics: list[dict]
) -> str:
    """Generate cover letter body text using Claude.

    Args:
        job_title: The job title
        company: Company name
        job_description: Full job description
        user_background: User's combined source documents
        cover_letter_topics: List of dicts with "topic" and "relevant_experience" keys

    Returns:
        Cover letter body text (without salutation/closing), or empty string on failure
    """
    if not job_description or not user_background or not cover_letter_topics:
        return ""

    # Format topics for the prompt
    topics_formatted = "\n".join(
        f"- Topic: {t['topic']}\n  Relevant experience: {t['relevant_experience']}"
        for t in cover_letter_topics
    )

    prompt = f"""Write a cover letter body for this job application.

CANDIDATE BACKGROUND:
{user_background}

JOB DETAILS:
Company: {company}
Position: {job_title}
Description:
{job_description}

KEY TOPICS TO ADDRESS (pre-analyzed, use these to structure the letter):
{topics_formatted}

INSTRUCTIONS:
- Write ONLY the body paragraphs (3-4 paragraphs)
- Do NOT include salutation (Dear...) or closing (Yours sincerely...)
- Use the pre-analyzed topics above to guide what you write about
- Don't try to hit every topic; focus on 3-4 strong connections
- Be specific: include metrics and concrete details from the relevant experience
- Keep it concise (250-350 words)
- Use contractions (I'm, I've, wasn't) for a natural tone
- Vary sentence and paragraph length deliberately

AVOID THESE AI WRITING PATTERNS:

1. Contrastive reframes: Never use "It wasn't just X, it was Y" or "This isn't about X, it's about Y". Just state what it is directly.

2. Negation for false depth: Avoid "more than just", "not only... but also", "not simply about". Make the point without the negation setup.

3. Rule of three: Don't use three parallel items for rhetorical effect ("expertise, passion, and commitment"). Use two items or four, or just one.

4. Paragraph-opening hedges: Never start with "When it comes to...", "In today's rapidly evolving...", "In the realm of...". Start with the actual subject.

5. Flattering intensifiers: Avoid "fascinating", "captivating", "remarkable", "compelling", "truly", "deeply", "genuinely". Don't call anything a "journey" or "transformation". Let facts speak.

6. Excessive transitions: Don't use "Furthermore", "Moreover", "Indeed", "In summary". Don't start multiple sentences with "This" referring back. If ideas connect, the connection should be obvious.

7. Mirrored structure: Don't make every paragraph the same length or follow the same pattern. A two-sentence paragraph followed by a longer one feels human.

8. Em-dashes: Use colons, commas, or periods instead of em-dashes (--).

9. Generic phrases: Never use "I am writing to apply", "aligns closely with", "I would welcome the opportunity", "I am excited to".

Write the cover letter body now:"""

    success, response = run_claude(prompt, timeout=120)

    if not success:
        return ""

    return response.strip()

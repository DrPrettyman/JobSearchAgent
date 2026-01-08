"""
Generate PDF cover letters from using LaTeX.
"""

import subprocess
import tempfile
import re
from datetime import datetime, timezone
from pathlib import Path

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

    @property
    def plain_text_cover_letter(self) -> str:
        """Generate plain text cover letter (no letterhead)."""
        lines = [
            f"Dear {self.addressee},",
            "",
            self.cover_letter_body,
            "",
            f"Yours {self.sign_off},",
            "",
            "Joshua Prettyman"
        ]
        return "\n".join(lines)

    def save_pdf(self, output_dir: Path):
        """Save PDF cover letter to file."""
        output_path = output_dir / f"{self.filename}.pdf"
        compile_latex_to_pdf(self.latex_source_cover_letter, output_path)
        
    def save_txt(self, output_dir: Path):
        txt_output_path = output_dir / f"{self.filename}.txt"
        txt_output_path.write_text(self.plain_text_cover_letter)

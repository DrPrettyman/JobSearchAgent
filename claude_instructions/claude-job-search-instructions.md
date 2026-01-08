# Claude Job Search Instructions

These instructions are for Claude to assist Joshua Prettyman in finding suitable job opportunities.

---

## Candidate Summary

**Name:** Joshua Prettyman, Ph.D.
**Current Role:** Data Freelancer (Jan 2025 - Present)
**Website:** [joshuaprettyman.com](https://joshuaprettyman.com)
**LinkedIn:** [linkedin.com/in/prettyman](https://www.linkedin.com/in/prettyman/)

### Professional Profile

Data Scientist with 10+ years of Python experience and a Ph.D. in Mathematics. Built an ML-powered SaaS platform from scratch that increased team productivity by 20x. Strong background in NLP, data engineering, full-stack development, and scientific computing. Published researcher with papers in Environmental Research Letters, Chaos, and Europhysics Letters.

---

## Location & Work Preferences

**Current Location:** Cártama, Málaga, Spain
**Nationality:** British
**Work Authorization:** EU/UK work rights

### Acceptable Work Arrangements (in order of preference):

1. **Remote** - Spanish company (fully remote)
2. **Remote** - UK company (fully remote)
3. **Remote** - Any company with "work from anywhere" policy
4. **Hybrid/On-site** - Málaga area only (willing to commute within Málaga province)

**Note:** Not open to relocation outside the Málaga area.

---

## Core Technical Skills

### Primary Stack (10+ years)
- **Python**: ScikitLearn, NumPy, Pandas, NLTK, Matplotlib, Plotly

### Data Science & ML
- Machine Learning (ScikitLearn, PyTorch, TensorFlow)
- NLP (NLTK, text processing, keyword clustering)
- LLM integrations (OpenAI API, Ollama, HuggingFace)
- Time series analysis, statistical modeling

### Data Engineering
- Cloud platforms: GCP (BigQuery, Compute Engine, Cloud Functions), AWS, Databricks
- Databases: PostgreSQL, BigQuery, SQL
- ETL/ELT pipelines, dbt
- API integrations: REST, GraphQL

### Full-Stack Development
- Backend: Python, Bash
- Frontend: JavaScript, Retool, Plotly dashboards
- Infrastructure: Docker, Git, CI/CD, Linux/Unix
- Async systems, job queues

### Visualization & Reporting
- Tableau, Looker, Retool
- Matplotlib, Plotly, Seaborn

### Additional Experience
- C++, MATLAB, R
- Scientific computing
- LaTeX, academic writing

---

## Professional Experience Summary

### Data Scientist at Blink SEO / Macaroni Software (Nov 2021 - Dec 2024)
- Built full-stack ML SaaS platform from scratch
- Increased team productivity by 20x
- Developed NLP-powered keyword clustering
- Architected Python backend on GCP processing 50M+ data points daily
- Created job-queue system (PostgreSQL) for async backend tasks
- Built interactive dashboards (Plotly + JavaScript)
- Integrated LLMs for content generation

### Data Science Researcher at National Physical Laboratory (Sep 2015 - Feb 2021)
- Developed novel scaling indicator for tipping point detection
- Published in peer-reviewed journals (ERL, Chaos, EPL)
- Time series analysis on large meteorological datasets
- Presented at international conferences

### Associate Lecturer at Sheffield Hallam University (Sep 2017 - Jul 2019)
- Taught mathematics, statistics, and computing (Foundation to Masters level)
- Course on Microsoft Excel for Business

### Informatics Developer at UK Met Office (Jun - Aug 2017)
- Data engineering internship
- API integrations (Java), data analysis (Python)

---

## Academic Background

- **Ph.D. Mathematics** - University of Reading
  - Thesis: "Tipping Points and Early Warning Signals with Applications to Geophysical Data"
  - 3 peer-reviewed publications

- **MRes Mathematics** - Imperial College London (Distinction)
  - Mathematics of Planet Earth CDT
  - Focus: Probability, Statistics, Computational Mathematics

- **MA Mathematics** - University of Edinburgh (First Class Honours)
  - Focus: Pure Mathematics and Mathematics Education

---

## Target Job Roles

Search for positions matching these titles (or similar):

- Data Scientist
- Senior Data Scientist
- Machine Learning Engineer
- ML Engineer
- Data Engineer
- Analytics Engineer
- Python Developer (data-focused)
- Full Stack Data Scientist
- Applied Scientist
- Research Scientist (industry)
- NLP Engineer
- AI Engineer

---

## Industry Preferences

Open to most industries, but particularly interested in:
- Technology / SaaS
- Climate / Environmental tech
- Marketing tech / SEO / Analytics
- Finance / Fintech
- Research institutions
- E-commerce
- Healthcare / Biotech

---

## Search Strategy for Claude

When searching for jobs, use queries such as:
- "remote data scientist Spain" OR "remote data scientist UK"
- "data scientist remote anywhere" OR "ML engineer remote worldwide"
- "data scientist Málaga" OR "machine learning engineer Andalucía"
- "Python developer remote Europe"
- "NLP engineer remote"
- Site-specific searches on LinkedIn, Indeed, RemoteOK, WeWorkRemotely, etc.

Use many different combinations to return relevant results. 

### Key Considerations When Evaluating Roles:
1. Must be remote OR based in Málaga area
2. Check if company hires in Spain/EU or UK
3. Look for mention of "work from anywhere" or specific country requirements
4. Senior/Mid-level roles preferred (3+ years experience required is fine)
5. Roles requiring heavy deep learning / computer vision are less suitable (NLP is fine)
6. Avoid roles requiring relocation outside Málaga
7. **Verify listings on the company's official careers page** before adding to jobs.json - job aggregators (WeWorkRemotely, Remotive, Remote Rocketship, etc.) often have stale listings that have been filled or removed

### CRITICAL: Link and Description Requirements

**DO NOT save a job unless you have BOTH:**

1. **A direct link to the specific job posting** - NOT:
   - A general company careers page (e.g., `company.com/careers/`)
   - A job board search results page (e.g., `linkedin.com/jobs/company-jobs`)
   - A job aggregator listing that may go stale

   The link must go directly to the individual job posting with its full description.

2. **An actual job description** - NOT:
   - A generic company description
   - A one-line summary you wrote yourself
   - A "talent community" or "future opportunities" page

   You must be able to read the actual responsibilities, requirements, and qualifications for the specific role.

**If you cannot find a direct job link or actual description, do not add the job to jobs.json.** It wastes time when the listing cannot be found or has already been filled.

---

## Source Files for More Details

If more detailed information is needed, refer to these files in the repository:

### CV & Experience
- `public/cv/two_page/JPrettymanCV.tex` - Full LaTeX CV with detailed experience
- `src/assets/cv-professional/manifest.json` - Professional experience overview
- `src/assets/cv-professional/blink.shtml` - Detailed Blink SEO/Macaroni experience
- `src/assets/cv-professional/npl.shtml` - NPL research experience
- `src/assets/cv-professional/freelance.shtml` - Current freelance services

### Academic Background
- `src/assets/cv-academic/manifest.json` - Education overview
- `src/assets/cv-academic/publications.json` - Full publication list with abstracts
- `src/assets/cv-academic/phd-reading.shtml` - Ph.D. details
- `src/assets/cv-academic/mres-imperial.shtml` - MRes details
- `src/assets/cv-academic/ma-edinburgh.shtml` - MA details

### Technical Skills
- `src/assets/techSkills.json` - Detailed breakdown of technical capabilities

---

## Output Format

When presenting job opportunities, include:
1. **Job Title** and **Company Name**
2. **Location** (Remote/Hybrid/On-site + any restrictions)
3. **Brief Description** of the role
4. **Why it's a good fit** (match with skills/experience)
5. **Link** - Direct application URL, or link to the job board/site where it was found (always required)
6. **Any concerns** (e.g., visa requirements, relocation expectations)

---

## Saving Jobs to jobs.json

When asked to save promising jobs, add them to `job_applications/jobs.json` with the following fields:

### Required Fields
- `company` - Company name
- `title` - Job title
- `date_found` - Date the job was found (YYYY-MM-DD format)
- `link` - **Direct URL to the specific job posting** (NOT a careers page or job board search)
- `description` - **The actual job description** with responsibilities and requirements (NOT a company summary)

### Optional Fields (include when available)
- `location` - Remote/Hybrid/On-site details
- `fit_notes` - Why this role is a good match
- `full_description` - Boolean indicating if full job description was successfully scraped (see scraping section below)
- `cover_letter` - If a cover letter has been drafted
- `questions` - Array of application questions and answers

### Pre-Save Checklist
Before adding a job, verify:
- [ ] The link goes directly to this specific job (not a careers landing page)
- [ ] You can see the full job description at that link
- [ ] The listing is still active (not expired/filled)
- [ ] The description field contains actual job requirements, not a company blurb

### Example Entry
```json
{
    "company": "Example Corp",
    "title": "Senior Data Scientist",
    "date_found": "2026-01-05",
    "link": "https://example.com/careers/job-id",
    "location": "Remote, Spain",
    "description": "Build ML models for...",
    "fit_notes": "Python and NLP experience align well."
}
```

---

## Full Description Scraping (Before Writing Cover Letters)

**IMPORTANT:** The WebFetch tool summarizes content, which can lose critical details from job descriptions. Before writing cover letters, use the scraping script to get the complete job description.

### Why This Matters
- WebFetch passes content through a summarization model
- Requirements, technologies, and qualifications may be omitted
- Missing a keyword could hurt your cover letter
- The full description may reveal deal-breakers not in the summary

### Process
After the initial job search and before writing cover letters:

1. **For each newly-added job**, run the scraping script:
   ```bash
   python3 job_applications/scrape_job.py "<job_url>"
   ```

2. **Compare the output** with the description you saved. Look for:
   - Additional requirements not captured
   - Specific technologies or tools mentioned
   - Company culture details
   - Salary information
   - Location restrictions

3. **Update the job entry in jobs.json** with any missing details that are relevant for the cover letter.

4. **Set the `full_description` field:**
   - `"full_description": true` - Script successfully returned complete job description
   - `"full_description": false` - Script failed (e.g., JavaScript-rendered pages like Workable) and manual verification is needed

### Known Limitations
Some job boards use heavy JavaScript rendering that prevents scraping:
- **Workable** (`apply.workable.com`) - Returns minimal content, requires manual check
- Other JS-heavy sites may also fail

For jobs with `"full_description": false`, you must manually visit the page and update the description before writing a cover letter.

### Example
```bash
python3 job_applications/scrape_job.py "https://jobs.lever.co/company/job-id"
```

This returns the full text content of the page, without summarization. Use this to ensure you have complete information before tailoring your cover letter.

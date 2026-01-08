# Job Search and Cover Letter Generation Task

You are helping Joshua Prettyman find data science jobs. This is a multi-step task that requires careful execution. Read this entire prompt before starting.

---

## PHASE 1: Read All Source Documents

Before doing anything else, read these files in full:

1. `job_applications/claude-job-search-instructions.md` - Job search criteria and strategy
2. `job_applications/claude-instructions.md` - Cover letter writing guidelines
3. `public/cv/two_page/JPrettymanCV.tex` - Current CV with accurate dates and details
4. `src/assets/techSkills.json` - Technical skills breakdown
5. `job_applications/jobs.json` - Existing applications for tone/style reference

After reading, confirm you understand:
- Joshua's location constraints (Málaga, Spain; remote Spain/UK/anywhere)
- Target job titles (Data Scientist, ML Engineer, etc.)
- Current employment status and dates (freelancing since Jan 2025)
- The cover letter style requirements (contractions, no em-dashes, no AI patterns)

---

## PHASE 2: Job Search

Search for jobs using MANY different query combinations. The queries in the instructions are EXAMPLES, not a complete list. You should run at least 15-20 different searches covering:

- Different job titles (Data Scientist, ML Engineer, NLP Engineer, AI Engineer, Analytics Engineer, Python Developer, etc.)
- Different location filters (remote Spain, remote UK, remote worldwide, Málaga, Andalucía)
- Different platforms (LinkedIn, Indeed, RemoteOK, WeWorkRemotely, company career pages, Greenhouse boards, Lever boards)
- Different industry focuses (fintech, climate tech, marketing tech, SaaS, etc.)

For EACH promising job found:
1. **Verify the listing exists** on the company's official careers page or a direct job posting URL
2. **Get the actual job description** - not a summary, the real listing with responsibilities and requirements
3. **Check location eligibility** - confirm they hire in Spain/EU or offer remote work from Spain
4. **Confirm the listing is current** - aggregator sites often have stale listings

**DO NOT add a job to jobs.json unless you have:**
- A direct link to the specific job posting (not a careers landing page)
- The actual job description text
- Confirmation the role is still open

In addition, also follow the guidelines in `job_applications/claude-job-search-instructions.md`.

---

## PHASE 3: Evaluate and Select Jobs

From your search results, select at least 10 jobs that:
- Match Joshua's skills (Python, ML, NLP, data engineering, production systems)
- Meet location requirements (remote or Málaga-based)
- Are appropriate seniority (mid to senior level)
- Have verifiable, active listings

For each selected job, add an entry to `jobs.json` with:
- `company`, `title`, `date_found` (today's date: YYYY-MM-DD format)
- `link` - direct URL to the job posting
- `location` - remote status and any restrictions
- `description` - the actual job description (abbreviated if very long, but include key requirements)
- `fit_notes` - brief note on why this matches Joshua's background

In addition, also follow the guidelines in `job_applications/claude-job-search-instructions.md`.

---

## PHASE 4: Scrape Full Job Descriptions

**IMPORTANT:** The WebFetch tool summarizes content, which can lose critical details. Before writing cover letters, scrape each newly-added job to get the complete description.

For each job you just added to jobs.json:

1. Run the scraping script:
   ```bash
   python3 job_applications/scrape_job.py "<job_url>"
   ```

2. Compare the output with the description you saved. Look for:
   - Additional requirements not captured by WebFetch
   - Specific technologies or tools mentioned
   - Company culture details
   - Salary information
   - Location restrictions or deal-breakers

3. Update the job entry in jobs.json with the FULL job description, plus any extra information about the company, location, etc..

4. Set the `full_description` field:
   - `"full_description": true` - Script successfully returned complete job description
   - `"full_description": false` - Script failed (e.g., Workable JS pages) and manual verification is needed

**Note:** Some job boards (like Workable) use JavaScript rendering that prevents scraping. For jobs with `"full_description": false`, flag them for manual verification and do not write cover letters until the description is confirmed.

This step ensures you have the fullest possible information before tailoring cover letters. WebFetch summaries may omit keywords, requirements, or context that could make or break your application.

---

## WARNING

For jobs with `"full_description": false`, STOP HERE. The following phases should be completed only after manual verification of the job description. 

For jobs with `"full_description": true`, continue to PHASE 5.

## PHASE 5: Create Cover Letter Topics

For each job, before writing the cover letter, create a `cover_letter_topics` array mapping job requirements to relevant experience. Look for:
- Explicit requirements from the job description
- Implicit requirements (company culture, team composition, industry context)
- Values or mission statements
- Technologies and methodologies mentioned

Each topic should map a job requirement to specific, concrete experience from Joshua's background.

In addition, also follow the guidelines in `job_applications/claude-instructions.md`.

---

## PHASE 6: Write Cover Letters

For each job, write a cover letter following these rules strictly:

**MUST DO:**
- Check `JPrettymanCV.tex` for accurate dates before writing
- Lead with industry experience for non-academic roles
- Use contractions (I'm, I've, wasn't)
- Include specific metrics (50M+ data points, 20x productivity)
- Vary sentence and paragraph length
- Connect past experience to specific job requirements
- Keep it to 4-6 short paragraphs

**MUST NOT:**
- Use em-dashes (use colons, commas, or periods instead)
- Use phrases like "I am writing to apply", "aligns closely with", "I would welcome the opportunity"
- List all three degrees (PhD is sufficient for industry roles)
- Use contrastive reframes ("It wasn't just X, it was Y")
- Use the rule of three for rhetorical effect
- Use flattering intensifiers (fascinating, remarkable, compelling, truly, deeply)
- Use excessive transitions (Furthermore, Moreover, Indeed)
- Make every paragraph the same length
- Misrepresent experience to match job terminology
- Include self-limiting language that rules Joshua out

**ACCURACY CHECK:**
- Joshua was at Blink SEO from Nov 2021 to Dec 2024
- He has been freelancing since Jan 2025
- Do NOT say "I've been building ML systems for the last three years" if the role ended

In addition, also follow the guidelines in `job_applications/claude-instructions.md`.

---

## PHASE 7: Quality Review

Before finalizing, review each cover letter for:

1. **AI pattern detection** - Read through the "AI writing patterns to avoid" section in `job_applications/claude-instructions.md` again and check each letter.
2. **Factual accuracy** - Verify dates and claims against the CV.
3. **Specific connection** - Each letter should reference something specific about that company/role.

---

## Expected Output

When complete, `jobs.json` should contain at least 10 NEW job entries (in addition to existing ones), each with:
- All required fields populated
- A verified, working link to the job posting
- A polished cover letter ready to submit

Report back with:
1. Summary of search queries used
2. List of jobs added with brief rationale for each
3. Any jobs you found but couldn't add (and why - e.g., couldn't verify listing, location ineligible)

---

## Important Reminders

- The search queries in the instructions are EXAMPLES. Use them as a starting point, then generate many more variations.
- Quality over quantity: 10 well-researched jobs with strong cover letters is better than 20 rushed entries.
- If you can't find a direct job link or verify a listing is active, skip that job entirely.
- Read the full job description before writing - don't write generic letters.
- Check your cover letters against the "AI patterns to avoid" checklist before saving.

Begin by reading all the source documents listed in Phase 1.

During context compaction always include this instruction: "If continuing from a compacted conversation, first read the full prompt for this task at `job_applications/claude-prompt.md`.".

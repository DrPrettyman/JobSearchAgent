# Cover Letter Writing Instructions

## Where to find information about Joshua

### Primary source (most up-to-date)
- **CV LaTeX file**: `public/cv/two_page/JPrettymanCV.tex`
  - Contains personal statement, technical skills, professional experience, and academic background
  - This is the canonical source for dates, job titles, and key achievements

### Additional detail
- **Technical skills breakdown**: `src/assets/techSkills.json`
  - Data Science: ScikitLearn, PyTorch, TensorFlow, NLP (NLTK), DBSCAN clustering, LLM integration (Ollama, Huggingface)
  - Data Engineering: BigQuery, PyGoogalytics package, GraphQL/REST API wrappers, ETL pipelines
  - Software Development: Python backend on GCP Compute Engine, PostgreSQL job queues, Scrapy, Cloud Functions
  - Visualisation: Matplotlib, Plotly, Retool dashboards, Looker Studio

- **Professional experience**: `src/assets/cv-professional/`
  - `blink.shtml` / `macaroni.shtml` - Blink SEO / Macaroni Software (most recent role)
  - `npl.shtml` - National Physical Laboratory (PhD research)
  - `shu.shtml` - Sheffield Hallam University (lecturing)
  - `met-office.shtml` - Met Office internship

- **Academic background**: `src/assets/cv-academic/`
  - `phd-reading.shtml` - PhD Mathematics, University of Reading
  - `mres-imperial.shtml` - MRes Mathematics, Imperial College London
  - `ma-edinburgh.shtml` - MA Mathematics, University of Edinburgh
  - `publications.json` - Published papers with links

### Previous applications
- **jobs.json** in this folder contains previous cover letters and question answers that can be referenced for tone and content

## Key selling points to highlight (adjust based on job requirements)

1. **Blink SEO / Macaroni Software**: Built full-stack ML platform from scratch, 20x productivity increase, Python backend on GCP + BigQuery (50M+ data points daily), async job queues in PostgreSQL, Plotly dashboards, evolved from internal tool to SaaS product

2. **PhD research at NPL**: Tipping point detection in time series data, stochastic models, published in peer-reviewed journals (ERL, Chaos, EPL), presented at international conferences

3. **Technical skills**: Python (10+ years), SQL, GCP, BigQuery, PostgreSQL, NLP, clustering, Plotly, Git, API integrations

4. **Soft skills**: Worked closely with delivery teams, comfortable explaining technical work to different audiences, ownership mentality

## Style guidelines

### Do
- Use contractions (I'm, I've, wasn't)
- Be direct and conversational
- Vary sentence length
- Include specific details (50M+ data points, 20x productivity)
- Show genuine interest in the specific role
- Connect past experience to the job requirements
- Keep it concise (4-6 short paragraphs)

### Don't
- Use em-dashes (use colons, commas, or periods instead)
- Use phrases like "I am writing to apply for...", "aligns closely with my experience", "I would welcome the opportunity"
- Use excessive formality or corporate-speak
- Make every paragraph the same length
- List skills like a checklist
- Over-explain or pad with filler
- Misrepresent experience to match job description terminology

### Accuracy and honesty

Do not stretch or misrepresent experience to match job description language. If the techniques are transferable but the application is different, say so honestly.

**Bad (misrepresenting experience):**
> "I wrote clustering models for customer segmentation (grouping keywords by search intent, weighted by volume)"

This incorrectly calls keyword clustering "customer segmentation". Customer segmentation means grouping customers by attributes or behaviour. Keyword clustering for SEO is a different application, even if it uses similar techniques.

**Good (honest about what it actually was):**
> "I built NLP clustering models and similarity matching using sklearn and text embeddings. The application was SEO rather than CRM, but the techniques overlap: grouping items by embedded features, scoring by weighted attributes, matching entities using centroid similarity."

This accurately describes what was built and acknowledges the techniques are transferable without claiming direct experience in customer segmentation.

### AI writing patterns to avoid

These sentence constructions are dead giveaways that AI wrote the text:

**Contrastive reframes ("It's not X, it's Y")**
- "It wasn't just a tool, it was a transformation"
- "The LLM integrations I shipped weren't demos, they were production features"
- "This isn't just about data, it's about impact"

Instead: Just say what it is. "I shipped LLM integrations to production" is fine.

**Negation for false depth ("more than just", "not only... but also")**
- "This role is more than just a job"
- "I'm not only a data scientist but also a problem solver"
- "It's not simply about building models"

Instead: Make the actual point without the negation setup.

**The Rule of Three**
- "I bring expertise in Python, passion for data, and commitment to excellence"
- "Speed, scale, and sustainability"
- Any time three parallel items appear for rhetorical effect

Instead: Two items or four. Or just one if that's all you need.

**Paragraph-opening hedges**
- "When it comes to..."
- "In today's rapidly evolving..."
- "In the realm of..."

Instead: Start with the actual subject.

**Flattering intensifiers**
- "Fascinating", "captivating", "remarkable", "compelling"
- "Truly", "deeply", "genuinely" (when not actually needed)
- Calling anything a "journey" or "transformation"

Instead: Let facts speak. If something is impressive, show why.

**Excessive transitions**
- "Furthermore", "Moreover", "Indeed", "In summary"
- Starting multiple sentences with "This" referring back

Instead: If ideas connect, the connection should be obvious. Cut the signposting.

**Mirrored structure across paragraphs**
- Every paragraph being roughly the same length
- Every paragraph following the same claim-evidence-conclusion pattern
- Repeating sentence rhythms

Instead: Vary structure deliberately. A two-sentence paragraph followed by a longer one feels human.

*Sources: [Blake Stockton](https://www.blakestockton.com/dont-write-like-ai-1-101-negation/), [Undetectable AI](https://undetectable.ai/blog/gpt-phrases/), [ProductiveShop](https://productiveshop.com/how-to-avoid-ai-writing-patterns/)*

### Structure (flexible, not a rigid template)
1. Opening: State interest and what specifically draws you to the role
2. Blink SEO experience: Relevant technical details, outcomes, what you enjoyed
3. PhD research: Connect to the role if relevant, otherwise keep brief
4. Skills summary: Brief, only if not already covered above
5. Closing: Simple, no grovelling

## Best practices from hiring managers (tech/data science roles)

### What matters most
1. **Quantify achievements**: Concrete numbers like "20x productivity increase" or "50M+ data points daily" provide clear evidence of impact. Hiring managers want to see measurable results, not vague claims.

2. **Show genuine interest in the specific company**: Generic letters get ignored. Reference something specific about what the company does or their goals. Show you understand their challenges.

3. **Lead with the strongest stuff**: Write the intro as if it's the only part they'll read. Don't bury achievements in paragraph three.

4. **Balance technical and soft skills**: Technical competence is assumed from the CV. The cover letter is a chance to show communication skills, collaboration, and how you work with others.

5. **Mirror the job description language**: If they say "deploy models to production", use that phrase. If they emphasise "cross-functional teams", address that directly.

6. **Keep it short**: Hiring managers spend under a minute on cover letters. 4-6 short paragraphs max. Every sentence should earn its place.

### Common mistakes to avoid
- Generic openings that could apply to any company
- Restating the CV instead of adding context
- Focusing only on what you want (growth, learning) rather than what you can contribute
- Listing technologies without showing what you did with them
- Being too humble or too boastful

### For career changers / non-traditional backgrounds
The cover letter is where you explain your journey and emphasise transferable skills. Joshua's PhD-to-industry path is a strength: it shows he can tackle novel problems, work independently, and communicate complex ideas.

*Sources: [Resume Worded](https://resumeworded.com/cover-letter-samples/data-scientist), [BrainStation](https://brainstation.io/career-guides/data-science-cover-letter-templates-and-examples), [365 Data Science](https://365datascience.com/career-advice/job-interview-tips/data-scientist-cover-letter/), [Indeed](https://www.indeed.com/career-advice/cover-letter-samples/data-scientist), [Teal](https://www.tealhq.com/cover-letter-examples/software-engineer)*

## Cover letter writing process

### Step 1: Analyse the job description

Before writing the cover letter, read the full job description carefully. Look for topics across:
- Company description and mission
- Sector/industry
- Team composition and culture
- Role responsibilities
- Required skills
- Nice-to-haves
- Any specific phrases or values mentioned

### Step 2: Create cover_letter_topics

Add a `cover_letter_topics` array to the job entry in jobs.json. Each topic should map a job requirement to relevant experience:

```json
"cover_letter_topics": [
    {
        "topic": "Proficiency in Python ecosystem (Pandas, Matplotlib, Scikit-Learn); deploying end-to-end ML models",
        "relevant_experience": "Built full ML platform at Blink processing 50M+ data points daily; NLP clustering, embeddings, sklearn"
    },
    {
        "topic": "sustainability sector",
        "relevant_experience": "MRes and PhD part of Mathematics of Planet Earth programme; PhD focused on tipping point detection in climate systems"
    },
    {
        "topic": "team of 20+ international Data Scientists from top academic institutions",
        "relevant_experience": "PhD from Reading/Imperial; published in peer-reviewed journals; presented at international conferences"
    }
]
```

Don't just list "Required Skills" verbatim. Also look for:
- Implicit requirements (e.g., "team of PhDs" implies academic background matters)
- Company values or mission statements
- Industry-specific context
- Team structure clues

### Step 3: Select the strongest points

Choose 3-5 topics where Joshua has the strongest, most specific experience. Prioritise:
- Topics where concrete metrics or outcomes can be cited
- Topics that differentiate Joshua from other candidates
- Topics the company emphasises most (mentioned multiple times, in headlines, etc.)

### Step 4: Write the cover letter

Use the selected topics to structure the letter. Don't try to hit every point. A focused letter with 3-4 strong connections beats a scattered letter trying to address everything.

## Example prompt

> Look at claude-instructions.md and write a cover letter for [Company Name]

Make sure the job entry in jobs.json has at minimum:
```json
{
    "company": "Company Name",
    "title": "Job Title",
    "description": "Full job description text..."
}
```

The cover letter will be added as a `"cover_letter"` field to the same entry.

## Critical rules (learned from past mistakes)

### 1. Read the CV for accurate dates

**ALWAYS** check `public/cv/two_page/JPrettymanCV.tex` for current employment dates before writing. Do not assume timelines.

**Bad:**
> "I've been building production ML systems in marketing tech for the last three years."

This was wrong because Blink SEO ended Dec 2024. Joshua has been freelancing since Jan 2025. The CV clearly shows:
- Data Freelancer: Jan. 2025 to Present
- Data Scientist at Blink SEO: Nov. 2021 to Dec. 2024

**Good:**
> "I spent three years at Blink SEO building production data systems, and I've been freelancing since early 2025."

### 2. Lead with industry experience for non-academic roles

For industry positions, lead with Blink/freelance experience. Mention PhD after industry experience, not before.

**Bad:**
> "My background is in mathematics: PhD from the University of Reading, MRes from Imperial College, MA from Edinburgh. I've spent the last three years in industry..."

**Good:**
> "The consulting model at Management Solutions interests me: at Blink I built a platform from scratch..."

### 3. Don't list all degrees

For industry roles, the PhD is sufficient. Listing MRes and MA with grades looks like padding.

**Bad:**
> "PhD from the University of Reading, MRes from Imperial College (Distinction), MA from Edinburgh (First Class)"

**Good:**
> "My PhD in Mathematics focused on time series analysis and tipping point detection"

### 4. Don't list irrelevant credentials

Only name specific journals, conferences, or institutions if they're relevant to the role. Otherwise, the general claim is sufficient.

**Bad (for an NLP/ML role):**
> "I published in peer-reviewed journals (Environmental Research Letters, Chaos, Europhysics Letters)"

These are geophysics journals. Listing them adds nothing for an NLP role and looks like padding.

**Good:**
> "I've published in peer-reviewed journals and presented at international conferences"

The point is to show academic rigor and communication skills. The specific names only matter if they strengthen the application for this particular role.

### 5. No self-limiting language

Never point out potential mismatches or rule yourself out. Let the CV speak for itself and let them decide.

**Bad:**
> "I notice this role targets recent graduates. I bring more experience than that, but I'm interested in consulting and would be glad to discuss whether there's a fit at a more senior level."

**Good:**
> "The exposure to high-profile projects and the partnership model both appeal to me."

### 6. Use colons to connect related sentences

Short related sentences should be joined with colons rather than left as choppy separate sentences.

**Bad:**
> "My PhD in Mathematics focused on time series analysis and tipping point detection. I used MATLAB for numerical simulations and published in peer-reviewed journals."

**Good:**
> "My PhD in Mathematics focused on time series analysis and tipping point detection: I used MATLAB for numerical simulations and published in peer-reviewed journals."

### 7. Avoid redundant openings

Don't waste the opening on throat-clearing. Lead directly with what draws you to the role.

**Bad:**
> "I spent three years at Blink SEO building production data systems, and I've been freelancing since early 2025. The consulting model at Management Solutions interests me."

**Good:**
> "The consulting model at Management Solutions interests me: at Blink I built a platform from scratch that processed 50M+ data points daily."

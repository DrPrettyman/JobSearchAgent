"""Shared prompt content for AI interactions."""

# These are the rules most often violated - placed prominently and checked explicitly
CRITICAL_WRITING_RULES = [
    """NO DRAMATIC COLONS: Never use "X: Y, Z, and W" to list things after a colon for effect.
BAD: "Wave's problem space: millions of users, sparse data, and complex tradeoffs"
GOOD: "Wave works with millions of users and sparse data, which requires..." """,
    """NO RULE OF THREE: Never list exactly three parallel items for rhetorical effect.
BAD: "expertise, passion, and commitment" / "scale, speed, and reliability"
GOOD: Use two items, four items, or just one. Two is usually enough.""",
    """DON'T DESCRIBE THE JOB BACK: The reader wrote the job description. Don't list what the job requires or what the company does—show how your experience connects.
BAD: "The role requires ML experience and working with large datasets"
BAD: "Wave operates in emerging markets with millions of users"
GOOD: "At Blink I built an ML pipeline processing 50M daily records, which taught me..." """,
    "NO FORMULAIC STRUCTURE: Don't start every paragraph with 'I'. Don't make paragraphs the same length. A two-sentence paragraph followed by a longer one feels human.",
    """NO EMPTY CONNECTORS: Cut "which is why", "this is what drew me to", "that's exactly what", "this is where". State the connection directly or let the reader infer it."""
]

AI_WRITING_GUIDELINES = [
    """Contrastive reframes: Never use "It wasn't just X, it was Y" or "This isn't about X, it's about Y". Just state what it is directly.""",
    """Negation for false depth: Avoid "more than just", "not only... but also", "not simply about". Make the point without the negation setup.""",
    """Rule of three: Don't use three parallel items for rhetorical effect ("expertise, passion, and commitment"). Use two items or four, or just one.""",
    """Paragraph-opening hedges: Never start with "When it comes to...", "In today's rapidly evolving...", "In the realm of...". Start with the actual subject.""",
    """Flattering intensifiers: Avoid "fascinating", "captivating", "remarkable", "compelling", "truly", "deeply", "genuinely". Don't call anything a "journey" or "transformation". Let facts speak.""",
    """Excessive transitions: Don't use "Furthermore", "Moreover", "Indeed", "In summary". Don't start multiple sentences with "This" referring back. If ideas connect, the connection should be obvious.""",
    "Mirrored structure: Don't make every paragraph the same length or follow the same pattern. A two-sentence paragraph followed by a longer one feels human.",
    "Em-dashes: Use colons, commas, or periods instead of em-dashes (--).",
    """Generic phrases: Never use "I am writing to apply", "aligns closely with", "I would welcome the opportunity", "I am excited to".""",
    """Hook lines with dramatic colons: Don't use "The problem was simple:" or "Here's the thing:" to create artificial tension. Write "The problem was that..." or just state the point directly.""",
    """LinkedIn buzzwords: Never use "at the intersection of", "in the X space", "leverage", "at scale", "ecosystem", "synergy", "thought leadership". These are content-marketing language, not human speech.""",
    """Empty intensifiers for experience: Don't say experience "runs deep", skills are "extensive", or background is "strong". Either give specifics or just state the fact plainly ("I've built APIs" not "My API experience runs deep").""",
    """Generic closings: Don't end with vague enthusiasm like "I'd like to help build whatever comes next" or "exactly where I want to be". End with something specific or just stop after your last substantive point.""",
    "Performative tone: Write as if speaking to one person, not posting content for an audience. If a sentence would work as a LinkedIn post, rewrite it.",
    """Indirect phrasing: Don't say "X is something I care about" or "Y is something I've always valued". Just state it directly: "I care about X" or better, show it through what you've done.""",
    """Formulaic paragraph starts: Don't start every paragraph with "I" or follow the same subject-verb pattern. Vary how paragraphs begin: start with the work, the company, a specific detail, or a short sentence that isn't "I [verb]".""",
]

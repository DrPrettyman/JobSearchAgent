import subprocess
import urllib.request
import re


def extract_url_slug(url: str) -> str:
    """Extract the last path segment from a URL.

    e.g.:
    - "https://github.com/torvalds" -> "torvalds"
    - "https://linkedin.com/in/prettyman/" -> "prettyman"
    - "username" -> "username"
    """
    return url.rstrip("/").split("/")[-1]


def run_claude(prompt: str, timeout: int = 120, tools: list[str] = None) -> tuple[bool, str]:
    """Run Claude CLI with a prompt. Returns (success, output).

    Args:
        prompt: The prompt to send to Claude
        timeout: Timeout in seconds
        tools: Optional list of tools to allow (e.g., ["WebSearch", "WebFetch"])
    """
    try:
        cmd = ["claude", "-p", prompt]
        if tools:
            cmd.extend(["--allowedTools", ",".join(tools)])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Timeout expired"
    except Exception as e:
        return False, str(e)
    
    
def scrape(url):
    """Fetch and extract text content from a job posting URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        response = urllib.request.urlopen(req, timeout=30)
        html = response.read().decode('utf-8')
    except Exception as e:
        raise RuntimeError(f"Error fetching URL: {e}")

    # Remove script and style tags
    html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL)

    # Remove HTML tags, replacing with newlines
    html_clean = re.sub(r'<[^>]+>', '\n', html_clean)

    # Clean up whitespace
    html_clean = re.sub(r'\n+', '\n', html_clean)
    html_clean = re.sub(r'[ \t]+', ' ', html_clean)

    # Decode HTML entities
    html_clean = html_clean.replace('&amp;', '&')
    html_clean = html_clean.replace('&lt;', '<')
    html_clean = html_clean.replace('&gt;', '>')
    html_clean = html_clean.replace('&quot;', '"')
    html_clean = html_clean.replace('&#39;', "'")
    html_clean = html_clean.replace('&nbsp;', ' ')

    # Extract lines and clean
    lines = [l.strip() for l in html_clean.split('\n') if l.strip()]

    return '\n'.join(lines)

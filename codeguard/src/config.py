import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # optional, increases rate limit
MODEL = "openai/gpt-oss-120b"

# token limits
MAX_FILES = 15
MAX_TOKENS_PER_FILE = 2000
MAX_TOTAL_TOKENS = 25000
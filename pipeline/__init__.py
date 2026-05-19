"""Promise Gap Analyser Pipeline Module."""

from .verdict import get_claude_verdict, MARKETING_VERDICT_LABELS
from .claude_verdict import classify_verdict, process_film, process_all_films

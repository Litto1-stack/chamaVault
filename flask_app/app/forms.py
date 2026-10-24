"""Tiny input-parsing helpers shared by routes."""
import re


def to_int(raw, lo=None, hi=None):
    """Parse a whole number (digits only, commas/spaces allowed); None if invalid or out of range."""
    cleaned = re.sub(r"[,\s]", "", raw or "")
    if not re.fullmatch(r"-?\d{1,9}", cleaned):
        return None
    n = int(cleaned)
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        return None
    return n

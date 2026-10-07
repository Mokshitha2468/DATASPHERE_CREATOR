"""Pattern learning from optional sample rows (CSV or JSON).

CRITICAL PRIVACY RULE:
Real sample rows are processed strictly in temporary memory to extract patterns.
They are IMMEDIATELY discarded and are NEVER stored in SharedState, logs,
LLM prompts, LangSmith traces, or frontend state.
"""

from __future__ import annotations
import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class ColumnPattern:
    """Statistical and structural pattern learned from sample rows."""
    min_length: int = 0
    max_length: int = 0
    prefix: str | None = None
    suffix: str | None = None
    date_format: str | None = None  # YYYYMMDD, YYYY-MM-DD, ISO, etc.
    min_date: date | None = None
    max_date: date | None = None
    numeric_min: float | None = None
    numeric_max: float | None = None
    is_numeric: bool = False
    flag_values: list[str] = field(default_factory=list)


@dataclass
class LearnedTablePatterns:
    """Collection of column patterns learned for a table + row hashes for collision avoidance."""
    columns: dict[str, ColumnPattern] = field(default_factory=dict)
    # Set of hashes of real rows to guarantee generated rows NEVER match real rows
    real_row_hashes: set[str] = field(default_factory=set)


def parse_and_learn_patterns(
    sample_content: str | bytes | list[dict[str, Any]] | None,
    max_rows: int = 20
) -> LearnedTablePatterns:
    """Inspects at most 20 sample rows in memory, extracts patterns, and discards real rows.
    
    Args:
        sample_content: Raw CSV string/bytes, JSON string/bytes, or list of dicts.
        max_rows: Maximum rows to inspect (capped at 20).
        
    Returns:
        LearnedTablePatterns: Extracted column patterns. No raw data is retained.
    """
    if not sample_content:
        return LearnedTablePatterns()

    rows: list[dict[str, Any]] = []

    # 1. Parse into memory (up to max_rows)
    try:
        if isinstance(sample_content, bytes):
            sample_content = sample_content.decode("utf-8", errors="ignore")

        if isinstance(sample_content, list):
            rows = sample_content[:max_rows]
        elif isinstance(sample_content, str):
            trimmed = sample_content.strip()
            if trimmed.startswith("[") or trimmed.startswith("{"):
                parsed = json.loads(trimmed)
                if isinstance(parsed, list):
                    rows = parsed[:max_rows]
                elif isinstance(parsed, dict):
                    rows = [parsed]
            else:
                # Parse as CSV
                reader = csv.DictReader(io.StringIO(trimmed))
                for idx, r in enumerate(reader):
                    if idx >= max_rows:
                        break
                    rows.append(dict(r))
    except Exception:
        # If parsing sample data fails, return empty patterns safely
        return LearnedTablePatterns()

    if not rows:
        return LearnedTablePatterns()

    result = LearnedTablePatterns()

    # Compute row hashes to prevent synthetic row collisions with real rows
    for r in rows:
        row_str = json.dumps(r, sort_keys=True, default=str)
        result.real_row_hashes.add(hashlib.sha256(row_str.encode("utf-8")).hexdigest())

    # Collect values per column
    col_values: dict[str, list[Any]] = {}
    for r in rows:
        for k, v in r.items():
            col_values.setdefault(k, []).append(v)

    # 2. Learn patterns per column
    for col_name, raw_vals in col_values.items():
        vals = [v for v in raw_vals if v is not None and str(v).strip() != ""]
        if not vals:
            continue

        pat = ColumnPattern()
        str_vals = [str(v).strip() for v in vals]
        lengths = [len(s) for s in str_vals]
        pat.min_length = min(lengths)
        pat.max_length = max(lengths)

        # Check for common fixed prefix (e.g. EMP_, US_, CUST-)
        if len(str_vals) >= 2:
            common_prefix = _find_common_prefix(str_vals)
            if len(common_prefix) >= 2 and any(c.isalpha() for c in common_prefix):
                pat.prefix = common_prefix

        # Check for 1-char flag values (e.g. ['X', ''], ['Y', 'N'])
        unique_vals = list(set(str_vals))
        if len(unique_vals) <= 3 and all(len(u) <= 1 for u in unique_vals):
            pat.flag_values = unique_vals

        # Check for numeric values
        num_vals: list[float] = []
        for s in str_vals:
            try:
                num_vals.append(float(s))
            except ValueError:
                pass
        if len(num_vals) == len(str_vals):
            pat.is_numeric = True
            pat.numeric_min = min(num_vals)
            pat.numeric_max = max(num_vals)

        # Check for date patterns (YYYYMMDD, YYYY-MM-DD, etc.)
        date_fmt, min_d, max_d = _detect_date_pattern(str_vals)
        if date_fmt:
            pat.date_format = date_fmt
            pat.min_date = min_d
            pat.max_date = max_d

        result.columns[col_name] = pat

    # Real rows are discarded as scope exits
    del rows
    return result


def _find_common_prefix(strings: list[str]) -> str:
    """Finds common fixed prefix across strings."""
    if not strings:
        return ""
    s1 = min(strings)
    s2 = max(strings)
    prefix = ""
    for i, c in enumerate(s1):
        if c != s2[i]:
            prefix = s1[:i]
            break
    else:
        prefix = s1
    # Strip trailing digits to extract clean prefix like EMP_ or CUST_
    cleaned = re.sub(r"\d+$", "", prefix)
    return cleaned if len(cleaned) >= 2 else prefix


def _detect_date_pattern(strings: list[str]) -> tuple[str | None, date | None, date | None]:
    """Detects date formatting and ranges from sample strings."""
    dates: list[date] = []
    
    # 1. YYYYMMDD (e.g. 20230115)
    if all(len(s) == 8 and s.isdigit() for s in strings):
        try:
            dates = [datetime.strptime(s, "%Y%m%d").date() for s in strings]
            return ("YYYYMMDD", min(dates), max(dates))
        except ValueError:
            pass

    # 2. YYYY-MM-DD
    if all(re.match(r"^\d{4}-\d{2}-\d{2}$", s) for s in strings):
        try:
            dates = [datetime.strptime(s, "%Y-%m-%d").date() for s in strings]
            return ("YYYY-MM-DD", min(dates), max(dates))
        except ValueError:
            pass

    # 3. DD.MM.YYYY
    if all(re.match(r"^\d{2}\.\d{2}\.\d{4}$", s) for s in strings):
        try:
            dates = [datetime.strptime(s, "%d.%m.%Y").date() for s in strings]
            return ("DD.MM.YYYY", min(dates), max(dates))
        except ValueError:
            pass

    return (None, None, None)

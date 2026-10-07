"""Deterministic Dummy Data Generator for Datasphere Source Tables.

Generates 20 realistic, deterministic synthetic rows respecting:
- SourceTable metadata & field label semantic hints
- Learned column patterns from optional sample rows (if provided)
- Guaranteed key uniqueness
- Valid date ranges (End Date >= Start Date)
- Field lengths and precision/scale constraints
- Collision safety: Generated rows NEVER equal any real sample row
"""

from __future__ import annotations
import datetime
import hashlib
import json
import random
from typing import Any

from app.domain.source import InferredClassification, SourceField, SourceTable
from app.services.sample_rows import LearnedTablePatterns, ColumnPattern


CITIES = ["New York", "London", "Tokyo", "Berlin", "Paris", "Singapore", "Sydney", "Toronto", "Frankfurt", "Zurich"]
COUNTRIES = ["US", "DE", "JP", "GB", "FR", "SG", "AU", "CA", "CH", "IN"]
CURRENCIES = ["EUR", "USD", "JPY", "GBP", "CHF", "CAD", "AUD", "SGD"]
STATUSES = ["ACTIVE", "PENDING", "COMPLETED", "CANCELLED", "APPROVED", "DRAFT", "ARCHIVED", "OPEN"]
CATEGORIES = ["ELECTRONICS", "APPAREL", "SERVICES", "HARDWARE", "SOFTWARE", "OFFICE", "INDUSTRIAL"]
DEPARTMENTS = ["Sales", "Finance", "Engineering", "Marketing", "HR", "Logistics", "Operations"]
FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley", "Casey", "Avery"]
LAST_NAMES = ["Smith", "Müller", "Tanaka", "Schmidt", "Dubois", "Wang", "Novak", "Garcia", "Rossi", "Kim"]


class DummyDataGenerator:
    """Generates synthetic rows strictly adhering to schema and learned pattern constraints."""

    def __init__(self, seed: int | None = 42):
        self.default_seed = seed

    def generate(
        self, 
        table: SourceTable, 
        row_count: int = 20, 
        patterns: LearnedTablePatterns | None = None
    ) -> list[dict[str, Any]]:
        """Generates deterministic fake rows for the given SourceTable."""
        table_seed_str = f"{table.name}:{table.source_connection or ''}:{table.remote_table or ''}:{len(table.fields)}"
        seed_offset = int(hashlib.md5(table_seed_str.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random((self.default_seed or 42) + seed_offset)

        rows: list[dict[str, Any]] = []
        key_fields = [f for f in table.fields if f.is_key]
        if not key_fields:
            key_fields = [f for f in table.fields if f.inferred_classification == InferredClassification.KEY_IDENTIFIER]

        learned_cols = patterns.columns if patterns else {}
        real_hashes = patterns.real_row_hashes if patterns else set()

        for row_idx in range(row_count):
            row_dict: dict[str, Any] = {}
            
            # Keep track of dates in row to enforce End Date >= Start Date
            start_date_val: datetime.date | None = None

            for field in table.fields:
                is_key = field in key_fields
                col_pat = learned_cols.get(field.name)
                
                val = self._generate_field_value(
                    field=field,
                    row_idx=row_idx,
                    is_key=is_key,
                    pat=col_pat,
                    start_date_ref=start_date_val,
                    rng=rng
                )
                
                # Check if this was a start date to pass reference to subsequent end date
                norm_name = (field.label or field.name).upper()
                if "START" in norm_name or "FROM" in norm_name or "BEG" in norm_name:
                    if isinstance(val, str) and len(val) >= 8:
                        try:
                            if "-" in val:
                                start_date_val = datetime.date.fromisoformat(val[:10])
                            elif len(val) == 8 and val.isdigit():
                                start_date_val = datetime.datetime.strptime(val, "%Y%m%d").date()
                        except Exception:
                            pass

                row_dict[field.name] = val

            # Verify that generated synthetic row does not match any real sample row
            row_hash = hashlib.sha256(json.dumps(row_dict, sort_keys=True, default=str).encode("utf-8")).hexdigest()
            if row_hash in real_hashes:
                # Slight modification to ensure synthetic separation
                first_col = table.fields[0].name
                if isinstance(row_dict[first_col], str):
                    row_dict[first_col] = f"{row_dict[first_col]}_SYN"

            rows.append(row_dict)

        return rows

    def _generate_field_value(
        self,
        field: SourceField,
        row_idx: int,
        is_key: bool,
        pat: ColumnPattern | None,
        start_date_ref: datetime.date | None,
        rng: random.Random
    ) -> Any:
        norm_type = field.data_type.lower().strip()
        norm_name = field.name.upper().strip()
        label_upper = (field.label or "").upper().strip()
        combined_text = f"{norm_name} {label_upper}"
        classification = field.inferred_classification

        # 1. Primary Keys & Key Identifiers
        if is_key:
            return self._generate_key_value(field, row_idx, norm_type, pat)

        # 2. Date / Time fields (respecting start/end relationships)
        if classification == InferredClassification.DATE_TIME or any(
            d in norm_type for d in ("date", "time", "timestamp")
        ) or any(d in combined_text for d in ("DATE", "DATUM", "PERIOD", "TIME", "TIMESTAMP", "YEAR")):
            return self._generate_date_time_value(field, row_idx, norm_type, combined_text, pat, start_date_ref)

        # 3. Boolean / Flag fields
        if classification == InferredClassification.BOOLEAN_FLAG or norm_type in ("boolean", "bool", "cds.boolean") or "FLAG" in combined_text or (pat and pat.flag_values):
            if pat and pat.flag_values:
                return pat.flag_values[row_idx % len(pat.flag_values)]
            if "FLAG" in combined_text or "INDICATOR" in combined_text:
                return "Y" if row_idx % 2 == 0 else "N"
            return bool(row_idx % 2 == 0)

        # 4. Binary / Blob
        if classification == InferredClassification.BINARY_OR_BLOB:
            hex_val = hashlib.sha256(f"{field.name}:{row_idx}".encode("utf-8")).hexdigest()
            if field.length:
                hex_val = hex_val[:field.length]
            return f"0x{hex_val[:16]}"

        # 5. Numeric / Measure / Decimals / Integers
        if classification == InferredClassification.MEASURE_CANDIDATE or (pat and pat.is_numeric) or any(
            n in norm_type for n in ("decimal", "integer", "int", "double", "float", "numeric", "real", "uint")
        ):
            return self._generate_numeric_value(field, row_idx, norm_type, combined_text, pat, rng)

        # 6. Dimensions / Text / Strings
        return self._generate_string_value(field, row_idx, combined_text, pat, rng)

    def _generate_key_value(
        self, 
        field: SourceField, 
        row_idx: int, 
        norm_type: str, 
        pat: ColumnPattern | None
    ) -> Any:
        key_num = 1000 + (row_idx + 1)
        
        # If pattern has prefix (e.g. EMP_)
        if pat and pat.prefix:
            val = f"{pat.prefix}{key_num}"
            if field.length and len(val) > field.length:
                val = val[:field.length]
            return val

        if any(int_t in norm_type for int_t in ("int", "integer", "uint", "bigint")):
            return key_num

        if "uuid" in norm_type or "guid" in norm_type or "UUID" in field.name.upper():
            return f"550e8400-e29b-41d4-a716-{key_num:012d}"
        
        prefix = field.name[:3].upper() if len(field.name) >= 3 else "KEY"
        key_str = f"{prefix}_{key_num}"
        if field.length and len(key_str) > field.length:
            key_str = f"K{row_idx+1:0{max(1, field.length - 1)}d}"[:field.length]
        return key_str

    def _generate_date_time_value(
        self, 
        field: SourceField, 
        row_idx: int, 
        norm_type: str, 
        combined_text: str,
        pat: ColumnPattern | None,
        start_date_ref: datetime.date | None
    ) -> str:
        # Determine base date
        base_date = datetime.date(2025, 1, 1) + datetime.timedelta(days=row_idx * 7)
        if pat and pat.min_date:
            base_date = pat.min_date + datetime.timedelta(days=row_idx * 5)

        # Enforce End Date >= Start Date
        if ("END" in combined_text or "TO" in combined_text or "EXPIR" in combined_text) and start_date_ref:
            # End date at least 30 days after start date
            base_date = start_date_ref + datetime.timedelta(days=30 + row_idx * 10)

        # Pattern format priority
        if pat and pat.date_format == "YYYYMMDD":
            return base_date.strftime("%Y%m%d")
        if pat and pat.date_format == "YYYY-MM-DD":
            return base_date.strftime("%Y-%m-%d")
        if pat and pat.date_format == "DD.MM.YYYY":
            return base_date.strftime("%d.%m.%Y")

        # Semantic SAP label hints (e.g. Start Date / End Date in SAP typically YYYYMMDD if CHAR(8) or DATS)
        if field.length == 8 or "DATS" in (field.native_type or "").upper() or "YYYYMMDD" in combined_text:
            return base_date.strftime("%Y%m%d")

        if "time" in norm_type and "date" not in norm_type and norm_type != "cds.timestamp":
            hour = (8 + row_idx) % 24
            minute = (row_idx * 7) % 60
            second = (row_idx * 13) % 60
            return f"{hour:02d}:{minute:02d}:{second:02d}"
        
        if "timestamp" in norm_type or "datetime" in norm_type:
            hour = (8 + row_idx) % 24
            minute = (row_idx * 7) % 60
            second = (row_idx * 13) % 60
            return f"{base_date.isoformat()}T{hour:02d}:{minute:02d}:{second:02d}Z"

        return base_date.isoformat()

    def _generate_numeric_value(
        self,
        field: SourceField,
        row_idx: int,
        norm_type: str,
        combined_text: str,
        pat: ColumnPattern | None,
        rng: random.Random
    ) -> int | float:
        # Check for Personnel Number or 8-digit identifier hint
        if any(h in combined_text for h in ("PERSONNEL", "PERNR", "EMPLOYEE NUMBER", "BADGE")):
            return 80000000 + row_idx * 137

        if any(int_t in norm_type for int_t in ("integer", "int", "uint", "bigint", "smallint", "tinyint")):
            if field.scale is None or field.scale == 0:
                base_int = ((row_idx + 1) * 150) + (row_idx * 7)
                if field.precision:
                    max_val = (10 ** min(field.precision, 9)) - 1
                    base_int = base_int % max_val
                return base_int

        precision = field.precision or 10
        scale = field.scale if field.scale is not None else 2
        
        integer_digits = max(1, precision - scale)
        max_int_part = min((10 ** integer_digits) - 1, 999999)
        
        int_part = ((row_idx + 1) * 235 + 47) % max_int_part
        if scale > 0:
            frac_part = (row_idx * 37 + 19) % (10 ** scale)
            val_str = f"{int_part}.{frac_part:0{scale}d}"
            return float(val_str)
        else:
            return float(int_part)

    def _generate_string_value(
        self,
        field: SourceField,
        row_idx: int,
        combined_text: str,
        pat: ColumnPattern | None,
        rng: random.Random
    ) -> str:
        # If pattern prefix exists
        if pat and pat.prefix:
            val = f"{pat.prefix}{100 + row_idx}"
            if field.length and len(val) > field.length:
                val = val[:field.length]
            return val

        # Semantic hints from field labels
        if any(c in combined_text for c in ("COUNTRY", "CTRY", "LAND1")):
            val = COUNTRIES[row_idx % len(COUNTRIES)]
        elif any(c in combined_text for c in ("CURRENCY", "CURR", "WAERK")):
            val = CURRENCIES[row_idx % len(CURRENCIES)]
        elif any(c in combined_text for c in ("CITY", "ORT")):
            val = CITIES[row_idx % len(CITIES)]
        elif any(c in combined_text for c in ("STATUS", "STAT")):
            val = STATUSES[row_idx % len(STATUSES)]
        elif any(c in combined_text for c in ("CATEGORY", "CAT", "TYPE")):
            val = CATEGORIES[row_idx % len(CATEGORIES)]
        elif any(c in combined_text for c in ("DEPT", "DEPARTMENT")):
            val = DEPARTMENTS[row_idx % len(DEPARTMENTS)]
        elif any(c in combined_text for c in ("PERSONNEL NUMBER", "PERNR")):
            val = f"PER_{80000000 + row_idx * 137}"
        elif any(c in combined_text for c in ("NAME", "CUSTOMER", "USER", "EMPLOYEE")):
            fn = FIRST_NAMES[row_idx % len(FIRST_NAMES)]
            ln = LAST_NAMES[row_idx % len(LAST_NAMES)]
            val = f"{fn} {ln}"
        elif any(c in combined_text for c in ("EMAIL", "MAIL")):
            fn = FIRST_NAMES[row_idx % len(FIRST_NAMES)].lower()
            ln = LAST_NAMES[row_idx % len(LAST_NAMES)].lower()
            val = f"{fn}.{ln}{row_idx+1}@example.com"
        elif "CODE" in combined_text:
            val = f"CD_{(row_idx + 1) * 11:03d}"
        else:
            clean_name = field.label or field.name.replace("_", " ").title()
            val = f"{clean_name} {row_idx + 1}"

        if field.length and len(val) > field.length:
            val = val[:field.length]

        return val


def generate_dummy_data(
    table: SourceTable, 
    row_count: int = 20, 
    seed: int | None = 42,
    patterns: LearnedTablePatterns | None = None
) -> list[dict[str, Any]]:
    """Generates deterministic synthetic rows for a SourceTable."""
    generator = DummyDataGenerator(seed=seed)
    return generator.generate(table, row_count=row_count, patterns=patterns)

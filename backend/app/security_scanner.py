"""
security_scanner.py
--------------------
Rule-based vulnerability detector.

GEN AI COURSE CONCEPT USED: Pattern matching / rule-based systems.
Before "learning" (ML) systems, most real-world security tools (and the
earliest AI systems in history!) work by matching known patterns —
this is the same logic behind regex-based NLP preprocessing you may have
covered: tokenizing text and matching it against known patterns.

Each rule = a regex pattern + metadata (category, severity, advice).
This is intentionally NOT machine learning — it's the "expert system"
style of AI, which is where AI as a field started before statistical/ML
approaches took over.
"""

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class Finding:
    line_number: int
    line_text: str
    category: str
    severity: str          # critical | high | medium | low
    rule_id: str
    message: str


# Each rule: (rule_id, category, severity, compiled_regex, message)
RULES = [
    (
        "SQLI-001",
        "SQL Injection",
        "critical",
        re.compile(r"(SELECT|INSERT|UPDATE|DELETE)\b.*(\+|\%|f['\"])", re.IGNORECASE),
        "User input appears to be concatenated directly into a SQL query.",
    ),
    (
        "SEC-001",
        "Hardcoded Secret",
        "critical",
        re.compile(r"(?i)(api_key|apikey|secret|password|token)\s*=\s*['\"][A-Za-z0-9_\-\.]{6,}['\"]"),
        "A credential or secret appears to be hardcoded directly in source code.",
    ),
    (
        "XSS-001",
        "Cross-Site Scripting",
        "high",
        re.compile(r"\.innerHTML\s*=\s*[^\"']"),
        "Assigning unsanitized data to innerHTML can allow script injection.",
    ),
    (
        "CRYPTO-001",
        "Weak Cryptography",
        "medium",
        re.compile(r"(?i)\b(md5|sha1)\s*\("),
        "MD5/SHA1 are cryptographically broken and unsuitable for security use.",
    ),
    (
        "EVAL-001",
        "Dangerous Eval",
        "high",
        re.compile(r"\beval\s*\("),
        "Use of eval() on dynamic input can lead to arbitrary code execution.",
    ),
    (
        "DESER-001",
        "Insecure Deserialization",
        "high",
        re.compile(r"\bpickle\.loads?\s*\("),
        "Deserializing untrusted data with pickle can execute arbitrary code.",
    ),
    (
        "AUTH-001",
        "Weak Authentication",
        "medium",
        re.compile(r"(?i)if\s+password\s*==\s*['\"]"),
        "Comparing plaintext passwords directly suggests passwords aren't hashed.",
    ),
    (
        "DEBUG-001",
        "Debug Mode Enabled",
        "low",
        re.compile(r"(?i)debug\s*=\s*True"),
        "Debug mode should never be enabled in production; it can leak stack traces.",
    ),
]


def scan_code(code: str) -> List[Finding]:
    """Run every rule against every line of the given source code."""
    findings: List[Finding] = []
    lines = code.splitlines()

    for i, line in enumerate(lines, start=1):
        for rule_id, category, severity, pattern, message in RULES:
            if pattern.search(line):
                findings.append(
                    Finding(
                        line_number=i,
                        line_text=line.strip(),
                        category=category,
                        severity=severity,
                        rule_id=rule_id,
                        message=message,
                    )
                )
    return findings


def risk_score(findings: List[Finding]) -> float:
    """Simple weighted score, 0-10. Same idea as a weighted sum in ML,
    just with hand-picked weights instead of learned ones."""
    weights = {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.5}
    raw = sum(weights.get(f.severity, 0) for f in findings)
    return round(min(raw, 10.0), 1)

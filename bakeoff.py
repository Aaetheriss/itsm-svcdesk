# ai-generated: 100% - ChatGPT implemented the published Lab 5 SARIF matching rules P-14 through P-23 and verified them on the practice set.
"""Convert SARIF scanner output plus course labels into a per-tool confusion matrix.

Usage:
    python3 -S -E bakeoff.py --labels labels.json a.sarif b.sarif

The implementation follows Laboratory 5 CI-SPEC.md rules P-14 through P-23.
Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote


COURSE_CLASSES: tuple[str, ...] = (
    "secret",
    "injection",
    "deserialization",
    "weak-crypto",
    "insecure-transport",
    "path-traversal",
    "ssrf",
    "vulnerable-dependency",
    "misconfiguration",
    "access-control",
)

CWE_TO_CLASSES: dict[int, tuple[str, ...]] = {}
for _class_name, _numbers in {
    "secret": (259, 260, 321, 798),
    "injection": (74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336),
    "deserialization": (502,),
    "weak-crypto": (261, 326, 327, 328, 330, 331, 338, 759, 760, 916),
    "insecure-transport": (295, 297, 319, 322, 757),
    "path-traversal": (22, 23, 35, 36, 73),
    "ssrf": (918,),
    "vulnerable-dependency": (937, 1035, 1104, 1395),
    "misconfiguration": (16, 215, 250, 489, 668, 732, 1188),
    "access-control": (284, 285, 639, 862, 863),
}.items():
    for _number in _numbers:
        CWE_TO_CLASSES.setdefault(_number, tuple())
        CWE_TO_CLASSES[_number] = (*CWE_TO_CLASSES[_number], _class_name)

KNOWN_TOOL_NAMES = {
    "trivy": "trivy",
    "grype": "grype",
    "osv-scanner": "osv-scanner",
    "gitleaks": "gitleaks",
    "semgrep": "semgrep",
    "semgrep oss": "semgrep",
    "semgrep ce": "semgrep",
    "semgrep community edition": "semgrep",
    "semgrep pro": "semgrep",
}

CWE_RE = re.compile(r"(?<![A-Za-z0-9])CWE-([0-9]+)", re.IGNORECASE)
TOKEN_RE = re.compile(r"[A-Za-z0-9._-]+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
PEP503_RE = re.compile(r"[-_.]+")


@dataclass(frozen=True)
class Finding:
    tool: str
    rule_id: str | None
    file: str
    start_line: int | None
    end_line: int | None
    classes: frozenset[str]
    message: str | None


@dataclass(frozen=True)
class Defect:
    index: int
    file: str
    class_name: str
    start_line: int | None
    end_line: int | None
    package: str | None


def _object(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _array(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _tool_id(run: dict[str, Any]) -> str:
    tool = _object(run.get("tool"))
    driver = _object(tool.get("driver")) if tool else None
    name = driver.get("name") if driver else None
    if not isinstance(name, str):
        return "unknown"
    stripped = name.strip()
    if not stripped:
        return "unknown"
    lowered = stripped.lower()
    known = KNOWN_TOOL_NAMES.get(lowered)
    if known is not None:
        return known
    normalized = NON_ALNUM_RE.sub("-", lowered).strip("-")
    return normalized or "unknown"


def _empty_suppressions(value: Any) -> bool:
    if value is None:
        return True
    if value is False or value == 0 or value == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def _rule_for_result(run: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    tool = _object(run.get("tool"))
    driver = _object(tool.get("driver")) if tool else None
    rules = _array(driver.get("rules")) if driver else []
    result_rule_id = result.get("ruleId")
    if result_rule_id is None:
        return None
    for entry in rules:
        rule = _object(entry)
        if rule is None:
            continue
        rule_id = rule.get("id")
        if rule_id is not None and type(rule_id) is type(result_rule_id) and rule_id == result_rule_id:
            return rule
    return None


def _string_tags(container: dict[str, Any] | None) -> list[str]:
    if container is None:
        return []
    properties = _object(container.get("properties"))
    if properties is None:
        return []
    return [tag for tag in _array(properties.get("tags")) if isinstance(tag, str)]


def _classes_for_result(tool_id: str, result: dict[str, Any], rule: dict[str, Any] | None) -> frozenset[str]:
    properties = _object(result.get("properties"))
    explicit = properties.get("class") if properties else None
    if isinstance(explicit, str) and explicit in COURSE_CLASSES:
        return frozenset((explicit,))

    if tool_id == "gitleaks":
        return frozenset(("secret",))
    if tool_id in {"grype", "osv-scanner"}:
        return frozenset(("vulnerable-dependency",))
    if tool_id == "trivy":
        mapped: list[str] = []
        for tag in _string_tags(rule):
            lowered = tag.lower()
            if lowered == "vulnerability" and "vulnerable-dependency" not in mapped:
                mapped.append("vulnerable-dependency")
            elif lowered == "secret" and "secret" not in mapped:
                mapped.append("secret")
            elif lowered == "misconfiguration" and "misconfiguration" not in mapped:
                mapped.append("misconfiguration")
        if mapped:
            return frozenset(mapped)

    mapped_classes: list[str] = []
    for tag in [*_string_tags(result), *_string_tags(rule)]:
        for match in CWE_RE.finditer(tag):
            number = int(match.group(1))
            for class_name in CWE_TO_CLASSES.get(number, ()):  # table order is stable
                if class_name not in mapped_classes:
                    mapped_classes.append(class_name)
    return frozenset(mapped_classes or ("other",))


def _normalize_path(uri: str, set_root: str) -> str | None:
    path = unquote(uri)
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]
    parts = path.split("/")
    last_index: int | None = None
    for index, component in enumerate(parts):
        if component == set_root:
            last_index = index
    if last_index is None:
        return None
    return "/".join(parts[last_index:])


def _line_region(physical_location: dict[str, Any]) -> tuple[int | None, int | None]:
    region = _object(physical_location.get("region"))
    if region is None:
        return None, None
    start = region.get("startLine")
    if type(start) is not int or start < 1:
        return None, None
    end = region.get("endLine")
    if type(end) is not int or end < start:
        end = start
    return start, end


def _message_text(result: dict[str, Any]) -> str | None:
    message = _object(result.get("message"))
    text = message.get("text") if message else None
    return text if isinstance(text, str) else None


def _iter_findings(document: dict[str, Any], set_root: str) -> tuple[set[str], list[Finding]]:
    tools: set[str] = set()
    findings: list[Finding] = []
    for run_value in _array(document.get("runs")):
        run = _object(run_value)
        if run is None:
            continue
        tool_id = _tool_id(run)
        tools.add(tool_id)
        for result_value in _array(run.get("results")):
            result = _object(result_value)
            if result is None:
                continue
            kind = result.get("kind")
            if kind is not None and kind != "fail":
                continue
            if not _empty_suppressions(result.get("suppressions")):
                continue
            locations = _array(result.get("locations"))
            if not locations:
                continue
            first_location = _object(locations[0])
            physical = _object(first_location.get("physicalLocation")) if first_location else None
            artifact = _object(physical.get("artifactLocation")) if physical else None
            uri = artifact.get("uri") if artifact else None
            if not isinstance(uri, str) or not uri:
                continue
            normalized_file = _normalize_path(uri, set_root)
            if normalized_file is None:
                continue
            start_line, end_line = _line_region(physical)
            rule = _rule_for_result(run, result)
            rule_id_value = result.get("ruleId")
            rule_id = rule_id_value if isinstance(rule_id_value, str) else None
            findings.append(
                Finding(
                    tool=tool_id,
                    rule_id=rule_id,
                    file=normalized_file,
                    start_line=start_line,
                    end_line=end_line,
                    classes=_classes_for_result(tool_id, result, rule),
                    message=_message_text(result),
                )
            )
    return tools, findings


def _normalize_package(value: str) -> str:
    return PEP503_RE.sub("-", value.lower())


def _message_names_package(message: str | None, package: str | None) -> bool:
    if message is None or package is None:
        return False
    wanted = _normalize_package(package)
    for raw_token in TOKEN_RE.findall(message):
        token = raw_token.strip("._-")
        if token and _normalize_package(token) == wanted:
            return True
    return False


def _finding_matches_defect(finding: Finding, defect: Defect) -> bool:
    if finding.file != defect.file or defect.class_name not in finding.classes:
        return False
    if defect.class_name == "vulnerable-dependency":
        return _message_names_package(finding.message, defect.package)
    if finding.start_line is None or finding.end_line is None:
        return False
    assert defect.start_line is not None and defect.end_line is not None
    return finding.start_line <= defect.end_line and defect.start_line <= finding.end_line


def _parse_defects(labels: dict[str, Any]) -> list[Defect]:
    defects: list[Defect] = []
    for index, value in enumerate(labels["defects"]):
        item = value
        class_name = item["class"]
        if class_name == "vulnerable-dependency":
            defects.append(
                Defect(
                    index=index,
                    file=item["file"],
                    class_name=class_name,
                    start_line=None,
                    end_line=None,
                    package=item["package"],
                )
            )
        else:
            defects.append(
                Defect(
                    index=index,
                    file=item["file"],
                    class_name=class_name,
                    start_line=item["start_line"],
                    end_line=item["end_line"],
                    package=None,
                )
            )
    return defects


def _rounded_score(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def confusion_matrix(labels: dict[str, Any], sarif_documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the matrix defined by CI-SPEC.md P-21 and P-22."""
    set_root = labels["set"]
    defects = _parse_defects(labels)
    tool_ids: set[str] = set()
    findings_by_tool: dict[str, list[Finding]] = {}

    for document in sarif_documents:
        document_tools, findings = _iter_findings(document, set_root)
        tool_ids.update(document_tools)
        for finding in findings:
            findings_by_tool.setdefault(finding.tool, []).append(finding)

    tools: dict[str, dict[str, int | float | None]] = {}
    for tool_id in sorted(tool_ids):
        matched_defects: set[int] = set()
        unmatched_fingerprints: set[tuple[str | None, str, int | None, int | None]] = set()
        for finding in findings_by_tool.get(tool_id, []):
            matches = [defect for defect in defects if _finding_matches_defect(finding, defect)]
            if matches:
                matched_defects.update(defect.index for defect in matches)
            else:
                unmatched_fingerprints.add(
                    (finding.rule_id, finding.file, finding.start_line, finding.end_line)
                )
        tp = len(matched_defects)
        fn = len(defects) - tp
        fp = len(unmatched_fingerprints)
        tools[tool_id] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": _rounded_score(tp, tp + fp),
            "recall": _rounded_score(tp, tp + fn),
            "f1": _rounded_score(2 * tp, 2 * tp + fp + fn),
        }

    return {"set": set_root, "defects": len(defects), "tools": tools}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="per-tool confusion matrix of SARIF against labels (CI-SPEC.md P-23)"
    )
    parser.add_argument("--labels", required=True, help="the labels file (P-14)")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)

    with open(args.labels, encoding="utf-8") as handle:
        labels = json.load(handle)
    documents: list[dict[str, Any]] = []
    for path in args.sarif:
        with open(path, encoding="utf-8") as handle:
            documents.append(json.load(handle))

    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

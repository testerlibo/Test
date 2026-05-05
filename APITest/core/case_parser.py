"""解析 AI 返回的用例：优先 JSON 数组（含 kind），失败则回退到「名称|params」旧格式。"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from core.result_judge import kind_from_case_name

CaseDict = Dict[str, Any]


def _strip_markdown_fence(text: str) -> str:
    s = text.strip()
    if not s.startswith("```"):
        return s
    lines = s.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _try_decode_json_array(text: str) -> Optional[List[Any]]:
    """从文本中解析第一个 JSON 数组（可含 markdown 代码围栏）。"""
    if not text or not text.strip():
        return None
    raw = _strip_markdown_fence(text.strip())
    start = raw.find("[")
    if start == -1:
        return None
    try:
        decoder = json.JSONDecoder()
        obj, _ = decoder.raw_decode(raw[start:])
        return obj if isinstance(obj, list) else None
    except json.JSONDecodeError:
        return None


def _normalize_kind(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in ("normal", "n", "positive", "正向", "正例"):
        return "normal"
    if s in ("negative", "neg", "abnormal", "异常", "反例", "负向"):
        return "negative"
    return None


def _validate_case_entry(obj: Any) -> Optional[CaseDict]:
    if not isinstance(obj, dict):
        return None
    kind = _normalize_kind(obj.get("kind"))
    name = obj.get("name")
    params = obj.get("params")
    if kind not in ("normal", "negative"):
        return None
    if not isinstance(name, str) or not name.strip():
        return None
    if not isinstance(params, dict):
        return None
    return {"kind": kind, "case": name.strip(), "params": params}


def parse_cases_from_ai(text: str) -> Tuple[List[CaseDict], List[str]]:
    """
    返回 (成功解析的用例列表, 告警信息列表)。
    先尝试 JSON 数组；失败则按行解析「名称|JSON对象」并推断 kind。
    """
    warnings: List[str] = []
    arr = _try_decode_json_array(text)
    if arr is not None:
        out: List[CaseDict] = []
        for i, item in enumerate(arr):
            row = _validate_case_entry(item)
            if row:
                out.append(row)
            else:
                warnings.append(f"JSON 第 {i + 1} 条无效，已跳过：{item!r}")
        if out:
            return out, warnings

    # 旧格式：每行 名称|params
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        try:
            case_name, param_str = line.split("|", 1)
            case_name = case_name.strip()
            params = json.loads(param_str.strip())
        except (json.JSONDecodeError, ValueError):
            warnings.append(f"行解析失败：{line[:80]}...")
            continue
        if not isinstance(params, dict):
            warnings.append(f"参数不是对象，跳过：{line[:80]}...")
            continue
        kind = kind_from_case_name(case_name)
        out.append({"kind": kind, "case": case_name, "params": params})

    if not out and text.strip():
        warnings.append("未能解析出任何用例（既非合法 JSON 数组，也无有效「名称|参数」行）")
    return out, warnings

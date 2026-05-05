"""统一「用例类型 kind + 返回 code」与预期是否一致的判定。"""
import re
from typing import Any, Dict, Literal

Kind = Literal["normal", "negative"]


def is_normal_case(case_name: str) -> bool:
    """根据用例标题推断是否为正向用例（旧格式兼容；新格式请直接传 kind）。"""
    s = (case_name or "").strip()
    return bool(re.match(r"^1[\s\.、]*正常", s))


def kind_from_case_name(case_name: str) -> Kind:
    return "normal" if is_normal_case(case_name) else "negative"


def expectation_met(resp: Dict[str, Any], kind: Kind) -> bool:
    """
    normal：期望业务成功 code == 0。
    negative：期望业务拒绝，code 存在且不为 0。
    """
    code = resp.get("code")
    if kind == "normal":
        return code == 0
    return code is not None and code != 0


def expectation_met_from_case_name(case_name: str, resp: Dict[str, Any]) -> bool:
    """旧数据或无 kind 字段时，根据用例名称推断 kind。"""
    return expectation_met(resp, kind_from_case_name(case_name))


def expectation_met_for_item(item: Dict[str, Any]) -> bool:
    """报告项：优先 item['kind']，否则根据 item['case'] 推断。"""
    kind = item.get("kind")
    if kind in ("normal", "negative"):
        return expectation_met(item["resp"], kind)
    return expectation_met_from_case_name(item.get("case") or "", item["resp"])

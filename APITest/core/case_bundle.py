"""将解析结果整理为固定结构：1 条 normal + 4 条 negative（不足时用内置模板补足）。"""
from __future__ import annotations

import copy
from typing import Dict, List, Tuple

from core.case_parser import CaseDict


def _builtin_negative_templates(default_params: Dict) -> List[CaseDict]:
    """生成至少 4 条可区分的负向模板（用于补足条数）。"""
    dp = default_params if isinstance(default_params, dict) else {}
    templates: List[CaseDict] = [
        {"kind": "negative", "case": "内置-空参", "params": {}},
    ]
    if not dp:
        while len(templates) < 4:
            n = len(templates)
            templates.append({"kind": "negative", "case": f"内置-占位{n}", "params": {}})
        return templates[:4]

    keys = list(dp.keys())
    d_drop = copy.deepcopy(dp)
    k0 = keys[0]
    d_drop.pop(k0, None)
    templates.append({"kind": "negative", "case": f"内置-缺少字段-{k0}", "params": d_drop})

    d_extra = copy.deepcopy(dp)
    d_extra["_invalid_extra_"] = True
    templates.append({"kind": "negative", "case": "内置-非法额外字段", "params": d_extra})

    d_bad = copy.deepcopy(dp)
    corrupted = False
    for k, v in list(d_bad.items()):
        if isinstance(v, int) and not isinstance(v, bool):
            d_bad[k] = -99999999
            templates.append({"kind": "negative", "case": f"内置-非法数值-{k}", "params": d_bad})
            corrupted = True
            break
        if isinstance(v, str):
            d_bad[k] = ""
            templates.append({"kind": "negative", "case": f"内置-空字符串-{k}", "params": d_bad})
            corrupted = True
            break
    if not corrupted:
        if "clientMeta" in dp and isinstance(dp.get("clientMeta"), dict):
            d_meta = copy.deepcopy(dp)
            d_meta["clientMeta"] = "invalid_type"
            templates.append(
                {"kind": "negative", "case": "内置-clientMeta类型错误", "params": d_meta}
            )
        else:
            templates.append({"kind": "negative", "case": "内置-空参B", "params": {}})

    while len(templates) < 4:
        templates.append(
            {"kind": "negative", "case": f"内置-补足{len(templates)}", "params": {}}
        )
    return templates[:4]


def ensure_one_normal_four_negative(
    parsed: List[CaseDict],
    default_params: Dict,
) -> Tuple[List[CaseDict], List[str]]:
    """
    返回恰好 5 条：[1 normal] + [4 negative]。
    - 多条 normal 只保留第一条；negative 多于 4 只保留前 4 条。
    - 缺少 normal 时用 default_params 构造一条。
    - negative 不足 4 时用内置模板按顺序补足。
    """
    warnings: List[str] = []
    normals = [x for x in parsed if x.get("kind") == "normal"]
    negatives = [x for x in parsed if x.get("kind") == "negative"]

    if len(normals) > 1:
        warnings.append(f"模型返回 {len(normals)} 条 normal，仅保留第 1 条")
    if len(negatives) > 4:
        warnings.append(f"模型返回 {len(negatives)} 条 negative，仅保留前 4 条")

    if normals:
        normal = copy.deepcopy(normals[0])
    else:
        warnings.append("未解析到 normal，使用配置中的默认参数作为正向用例")
        normal = {
            "kind": "normal",
            "case": "正常-默认参数",
            "params": copy.deepcopy(default_params) if isinstance(default_params, dict) else {},
        }

    neg_chosen = copy.deepcopy(negatives[:4])
    need = 4 - len(neg_chosen)
    if need > 0:
        warnings.append(f"negative 缺 {need} 条，已用内置模板补足")
        pool = _builtin_negative_templates(default_params)
        for j in range(need):
            neg_chosen.append(copy.deepcopy(pool[j % len(pool)]))

    out = [normal] + neg_chosen[:4]
    assert len(out) == 5
    return out, warnings

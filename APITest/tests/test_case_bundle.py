import copy

from core.case_bundle import ensure_one_normal_four_negative


def _row(kind, name, params):
    return {"kind": kind, "case": name, "params": params}


def test_always_five_one_normal_four_negative():
    default = {"x": 1, "y": 2}
    out, w = ensure_one_normal_four_negative([], default)
    assert len(out) == 5
    assert out[0]["kind"] == "normal"
    assert out[0]["params"] == default
    assert sum(1 for r in out if r["kind"] == "negative") == 4
    assert any("未解析到 normal" in x for x in w)


def test_trim_extra_normals_and_negatives():
    default = {"a": 1}
    parsed = [
        _row("normal", "n1", {"a": 1}),
        _row("normal", "n2", {"a": 2}),
        _row("negative", "e1", {}),
        _row("negative", "e2", {}),
        _row("negative", "e3", {}),
        _row("negative", "e4", {}),
        _row("negative", "e5", {}),
    ]
    out, w = ensure_one_normal_four_negative(parsed, default)
    assert len(out) == 5
    assert out[0]["case"] == "n1"
    assert [r["case"] for r in out[1:]] == ["e1", "e2", "e3", "e4"]
    assert any("仅保留" in x for x in w)


def test_pad_negatives():
    default = {"k": 1}
    parsed = [_row("normal", "ok", {"k": 1}), _row("negative", "only", {})]
    out, w = ensure_one_normal_four_negative(parsed, default)
    assert len(out) == 5
    assert out[0]["case"] == "ok"
    assert sum(1 for r in out[1:] if r["kind"] == "negative") == 4
    assert any("补足" in x for x in w)

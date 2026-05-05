from core.case_parser import parse_cases_from_ai


def test_parse_json_array():
    text = """
以下是结果：
[
  {"kind": "normal", "name": "a", "params": {"x": 1}},
  {"kind": "negative", "name": "b", "params": {}}
]
"""
    cases, warns = parse_cases_from_ai(text)
    assert len(cases) == 2
    assert cases[0]["kind"] == "normal"
    assert cases[0]["params"] == {"x": 1}
    assert cases[1]["kind"] == "negative"
    assert warns == []


def test_parse_markdown_fence():
    text = """```json
[
  {"kind": "normal", "name": " fenced ", "params": {"x": 1}}
]
```"""
    cases, warns = parse_cases_from_ai(text)
    assert len(cases) == 1
    assert cases[0]["kind"] == "normal"
    assert cases[0]["case"] == "fenced"
    assert warns == []


def test_parse_legacy_pipe_lines():
    text = """1 正常用例|{"a": 1}
2 空参|{}"""
    cases, warns = parse_cases_from_ai(text)
    assert len(cases) == 2
    assert cases[0]["kind"] == "normal"
    assert cases[1]["kind"] == "negative"
    assert cases[1]["params"] == {}
    assert isinstance(warns, list)


def test_normalize_kind_aliases():
    text = '[{"kind":"正向","name":"t","params":{}}]'
    cases, _ = parse_cases_from_ai(text)
    assert len(cases) == 1
    assert cases[0]["kind"] == "normal"


def test_invalid_rows_skipped_with_warning():
    text = '[{"kind":"normal","name":"","params":{}},{"kind":"negative","name":"ok","params":{}}]'
    cases, warns = parse_cases_from_ai(text)
    assert len(cases) == 1
    assert cases[0]["case"] == "ok"
    assert any("无效" in w or "跳过" in w for w in warns)

import pytest

from core.result_judge import (
    expectation_met,
    expectation_met_for_item,
    expectation_met_from_case_name,
    is_normal_case,
    kind_from_case_name,
)


@pytest.mark.parametrize(
    "name, want",
    [
        ("1 正常用例", True),
        ("1. 正常用例", True),
        ("1、正常", True),
        ("1 正常", True),
        ("2 空参", False),
        ("12 正常用例", False),
        ("", False),
    ],
)
def test_is_normal_case(name, want):
    assert is_normal_case(name) is want


def test_kind_from_case_name():
    assert kind_from_case_name("1 正常用例") == "normal"
    assert kind_from_case_name("2 空参") == "negative"


@pytest.mark.parametrize(
    "kind, resp, met",
    [
        ("normal", {"code": 0}, True),
        ("normal", {"code": 1}, False),
        ("normal", {}, False),
        ("negative", {"code": 1001}, True),
        ("negative", {"code": 0}, False),
        ("negative", {}, False),
    ],
)
def test_expectation_met(kind, resp, met):
    assert expectation_met(resp, kind) is met


def test_expectation_met_from_case_name():
    assert expectation_met_from_case_name("1 正常用例", {"code": 0}) is True
    assert expectation_met_from_case_name("1 正常用例", {"code": 3}) is False
    assert expectation_met_from_case_name("3 缺参", {"code": 4001}) is True
    assert expectation_met_from_case_name("3 缺参", {"code": 0}) is False


def test_expectation_met_for_item_prefers_kind():
    item = {"case": "xxx", "kind": "normal", "resp": {"code": 1}}
    assert expectation_met_for_item(item) is False

    item2 = {"case": "1 正常用例", "kind": "negative", "resp": {"code": 0}}
    assert expectation_met_for_item(item2) is False  # kind overrides misleading title

    item3 = {"case": "3 缺参", "resp": {"code": 10}}
    assert expectation_met_for_item(item3) is True


def test_expectation_met_for_item_legacy_without_kind():
    item = {"case": "1 正常用例", "resp": {"code": 0}}
    assert expectation_met_for_item(item) is True

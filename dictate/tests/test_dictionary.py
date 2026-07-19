from __future__ import annotations

import json

import pytest

from dictate.dictionary import Dictionary, DictionaryError


def test_single_word_override_case_insensitive():
    d = Dictionary({"jason": "JSON"})
    assert d.apply("parse the Jason file") == "parse the JSON file"


def test_multi_word_override():
    d = Dictionary({"get hub": "GitHub"})
    assert d.apply("push it to get hub now") == "push it to GitHub now"


def test_word_boundaries_respected():
    d = Dictionary({"jason": "JSON"})
    assert d.apply("jasonette stays") == "jasonette stays"


def test_longest_match_wins():
    d = Dictionary({"post": "POST", "post gress": "Postgres"})
    assert d.apply("use post gress here") == "use Postgres here"
    assert d.apply("send a post request") == "send a POST request"


def test_empty_dictionary_is_identity():
    d = Dictionary({})
    assert d.apply("hello world") == "hello world"


def test_load_missing_file_returns_empty(tmp_path):
    d = Dictionary.load(tmp_path / "nope.json")
    assert d.apply("get hub") == "get hub"


def test_load_valid_file(tmp_path):
    path = tmp_path / "dict.json"
    path.write_text(json.dumps({"overrides": {"pie torch": "PyTorch"}}))
    d = Dictionary.load(path)
    assert d.apply("install pie torch") == "install PyTorch"


def test_load_malformed_json_raises_with_filename(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    with pytest.raises(DictionaryError, match="bad.json"):
        Dictionary.load(path)


def test_load_wrong_shape_raises(tmp_path):
    path = tmp_path / "shape.json"
    path.write_text(json.dumps({"overrides": ["not", "a", "mapping"]}))
    with pytest.raises(DictionaryError, match="shape.json"):
        Dictionary.load(path)


def test_apply_empty_text():
    d = Dictionary({"a": "b"})
    assert d.apply("") == ""

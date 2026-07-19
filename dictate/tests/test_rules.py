from __future__ import annotations

from dictate.polish.rules import RulePolisher


def polish(text: str, **kwargs) -> str:
    return RulePolisher(**kwargs).polish(text)


def test_spec_ac2_filler_sentence():
    assert (
        polish("um so basically the uh meeting is tomorrow")
        == "The meeting is tomorrow."
    )


def test_removes_common_fillers():
    assert polish("uh I think um it works") == "I think it works."


def test_filler_word_boundaries():
    assert polish("bring an umbrella") == "Bring an umbrella."


def test_filler_only_input_yields_empty():
    assert polish("um uh umm") == ""


def test_empty_input():
    assert polish("") == ""


def test_capitalizes_sentence_starts():
    assert polish("hello world. how are you") == "Hello world. How are you."


def test_keeps_existing_terminal_punctuation():
    assert polish("is it done?") == "Is it done?"
    assert polish("stop that!") == "Stop that!"


def test_standalone_i_capitalized():
    assert polish("i think i can") == "I think I can."


def test_collapses_whitespace_and_fixes_punctuation_spacing():
    assert polish("hello  ,  world .  yes") == "Hello, world. Yes."


def test_cleans_up_commas_left_by_filler_removal():
    assert polish("um, so basically, it works") == "It works."


def test_preserves_proper_noun_casing():
    assert polish("push to GitHub tomorrow") == "Push to GitHub tomorrow."


def test_extra_fillers_configurable():
    assert polish("well it works", extra_fillers=("well",)) == "It works."


def test_removes_phrase_fillers():
    assert polish("you know it just works i mean mostly") == "It just works mostly."

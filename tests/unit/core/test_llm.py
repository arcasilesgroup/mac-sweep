"""Tests for mac_sweep.core.llm."""

from mac_sweep.core.llm import _build_candidates_text, _parse_llm_response
from mac_sweep.core.models import CleanupCandidate


class TestParseLlmResponse:
    def test_valid_json(self):
        result = _parse_llm_response('{"items": ["hugo", "Warp"]}')
        assert result == ["hugo", "Warp"]

    def test_empty_items(self):
        result = _parse_llm_response('{"items": []}')
        assert result == []

    def test_json_in_code_block(self):
        text = '```json\n{"items": ["hugo"]}\n```'
        result = _parse_llm_response(text)
        assert result == ["hugo"]

    def test_json_with_surrounding_text(self):
        text = 'Here are the items: {"items": ["hugo"]} hope this helps!'
        result = _parse_llm_response(text)
        assert result == ["hugo"]

    def test_invalid_json(self):
        result = _parse_llm_response("not json at all")
        assert result is None

    def test_missing_items_key(self):
        result = _parse_llm_response('{"packages": ["hugo"]}')
        assert result is None

    def test_items_not_list(self):
        result = _parse_llm_response('{"items": "hugo"}')
        assert result is None

    def test_non_string_items_filtered(self):
        result = _parse_llm_response('{"items": ["hugo", 123, "Warp"]}')
        assert result == ["hugo", "Warp"]

    def test_deeply_nested_code_block(self):
        text = 'Sure!\n```\n{"items": ["Slack"]}\n```\nDone.'
        result = _parse_llm_response(text)
        assert result == ["Slack"]

    def test_multiple_json_objects(self):
        text = '{"other": 1} {"items": ["hugo"]}'
        result = _parse_llm_response(text)
        # Multiple JSON objects in a string is not valid JSON
        # so the parser cannot reliably extract the right one
        assert result is None


class TestBuildCandidatesText:
    def test_formats_candidates(self):
        candidates = [
            CleanupCandidate(
                name="hugo", category="Homebrew Formula",
                description="Static site generator", status="Dormant",
                removal_method="brew_formula",
                removal_cmd=("brew", "uninstall", "hugo"),
                undo_cmd=("brew", "install", "hugo"),
            ),
            CleanupCandidate(
                name="Warp", category="GUI Application",
                description="Terminal", status="Dormant",
                removal_method="brew_cask",
                removal_cmd=("brew", "uninstall", "--cask", "warp"),
                undo_cmd=("brew", "install", "--cask", "warp"),
            ),
        ]
        text = _build_candidates_text(candidates)
        assert "hugo" in text
        assert "Warp" in text
        assert "Homebrew Formula" in text
        assert "GUI Application" in text
        assert "Dormant" in text

    def test_empty_candidates(self):
        text = _build_candidates_text([])
        assert text == ""

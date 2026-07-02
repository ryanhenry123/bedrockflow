import pytest

from orchflow.cli import main


def test_eval_cli_good_fixture(capsys):
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "eval",
                "tests/fixtures/good_memo.md",
                "--ctx",
                '{"evidence_years":[2024,2026],"max_words":600,"min_words":100,"min_trades":1}',
            ]
        )
    out = capsys.readouterr().out
    assert exc.value.code == 0
    assert "good_memo.md: ok" in out


def test_eval_cli_bad_fixture_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["eval", "tests/fixtures/bad_memo.md"])
    out = capsys.readouterr().out
    assert exc.value.code == 1
    assert "bad_memo.md: retry" in out
    assert "  - " in out

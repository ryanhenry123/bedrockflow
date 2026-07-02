from orchflow.evals.context import Context
from orchflow.evals.verdict import EvalVerdict, run_panel
from conftest import MockResult


def ok(_ctx, _result):
    return EvalVerdict.OK


def retry_with_feedback(ctx, _result):
    ctx.feedback("too short")
    return EvalVerdict.RETRY


def retry_silent(_ctx, _result):
    return EvalVerdict.RETRY


def fail(_ctx, _result):
    return EvalVerdict.FAIL


def test_panel_ok():
    verdict, reasons = run_panel([ok, ok], Context(), MockResult("fine"))
    assert verdict is EvalVerdict.OK
    assert reasons == []


def test_panel_collects_multiple_retry_reasons():
    ctx = Context()

    def a(c, _r):
        c.feedback("first")
        return EvalVerdict.RETRY

    def b(c, _r):
        c.feedback("second")
        return EvalVerdict.RETRY

    verdict, reasons = run_panel([a, b], ctx, MockResult("x"))
    assert verdict is EvalVerdict.RETRY
    assert reasons == ["first", "second"]


def test_panel_fail_stops_early():
    verdict, reasons = run_panel(
        [retry_with_feedback, fail], Context(), MockResult("x")
    )
    assert verdict is EvalVerdict.FAIL
    assert reasons == ["too short"]


def test_panel_retry_without_feedback_gets_default_reason():
    verdict, reasons = run_panel([retry_silent], Context(), MockResult("x"))
    assert verdict is EvalVerdict.RETRY
    assert reasons == ["revision requested"]

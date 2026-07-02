from os import getenv

DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-6"


def resolve_model_id(
    member: str = "ANTHROPIC_CLAUDE_SONNET_4_6",
    *,
    fallback: str = DEFAULT_MODEL,
) -> str:
    try:
        from orchflow.providers.aws._gen_foundation_catalog import FoundationModelId

        return getattr(FoundationModelId, member).value
    except (ImportError, AttributeError):
        return fallback


MODEL = getenv("ORCHFLOW_MODEL", resolve_model_id())

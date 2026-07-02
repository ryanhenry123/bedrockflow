from dataclasses import dataclass


@dataclass(frozen=True)
class MockResult:
    text: str
    stop_reason: str = "end_turn"
    output_tokens: int | None = None
    input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    cache_write_input_tokens: int | None = None

    @property
    def usage(self):
        if self.output_tokens is None and self.input_tokens is None:
            return None

        @dataclass(frozen=True)
        class U:
            output_tokens: int
            input_tokens: int
            cache_read_input_tokens: int | None = None
            cache_write_input_tokens: int | None = None

        return U(
            output_tokens=self.output_tokens or 0,
            input_tokens=self.input_tokens or 0,
            cache_read_input_tokens=self.cache_read_input_tokens,
            cache_write_input_tokens=self.cache_write_input_tokens,
        )

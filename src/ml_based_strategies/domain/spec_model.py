"""Base model for edge schemas: files, decide() I/O, LLM output."""

from pydantic import BaseModel, ConfigDict


class SpecModel(BaseModel):
    # forbid for clearing typos
    model_config = ConfigDict(frozen=True, extra="forbid")

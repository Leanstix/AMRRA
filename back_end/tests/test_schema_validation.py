import pytest
from pydantic import ValidationError

from app.domain.schemas import Observation, SourceInput


def test_text_source_requires_content():
    with pytest.raises(ValidationError):
        SourceInput(kind="text", content="")


def test_observation_confidence_is_bounded():
    with pytest.raises(ValidationError):
        Observation(name="x", confidence=1.2)

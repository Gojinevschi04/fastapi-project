from unittest.mock import MagicMock

import pytest

from app.core.repositories import Repository


class ConcreteRepository(Repository):
    pass


def test_repository_initialization(mock_session: MagicMock) -> None:
    repo = ConcreteRepository(session=mock_session)
    assert repo._session == mock_session


def test_repository_has_session(mock_session: MagicMock) -> None:
    repo = ConcreteRepository(session=mock_session)
    assert hasattr(repo, "_session")

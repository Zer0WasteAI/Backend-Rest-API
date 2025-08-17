from types import SimpleNamespace
from unittest.mock import MagicMock


class FakeResult:
    def __init__(self, fetchone=None, fetchall=None):
        self._one = fetchone
        self._all = fetchall or []
    def fetchone(self):
        return self._one
    def fetchall(self):
        return self._all


class FakeSession:
    def __init__(self):
        self.execute = MagicMock(return_value=FakeResult())
        self.commit = MagicMock()


class FakeDB:
    def __init__(self, session):
        self.session = session


def make_generation_row():
    return SimpleNamespace(uid='g1', user_uid='u1', generated_at=None,
                           raw_result={}, generation_type='t', recipes_ids=None,
                           is_validated=False, validated_at=None)


def test_generation_save_insert_commits():
    from src.infrastructure.db.generation_repository_impl import GenerationRepositoryImpl
    from src.domain.models.generation import Generation
    session = FakeSession()
    # find_by_uid will return None (default FakeResult has None)
    db = FakeDB(session)
    repo = GenerationRepositoryImpl(db)
    g = Generation(uid='g1', user_uid='u1', generated_at=None, raw_result={}, generation_type='t', recipes_ids=None, is_validated=False, validated_at=None)
    repo.save(g)
    session.commit.assert_called_once()


def test_generation_find_by_user_and_uid_and_update_validation():
    from src.infrastructure.db.generation_repository_impl import GenerationRepositoryImpl
    session = FakeSession()
    row = make_generation_row()
    session.execute.side_effect = [
        FakeResult(fetchall=[(row,)]),  # find_by_user
        FakeResult(fetchone=(row,)),    # find_by_uid
        FakeResult(),                   # update_validation_status
    ]
    db = FakeDB(session)
    repo = GenerationRepositoryImpl(db)
    lst = repo.find_by_user('u1')
    assert len(lst) == 1 and lst[0].uid == 'g1'
    one = repo.find_by_uid('g1')
    assert one.uid == 'g1'
    repo.update_validation_status('g1', True)
    session.commit.assert_called()


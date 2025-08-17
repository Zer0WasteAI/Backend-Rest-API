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
        self.rollback = MagicMock()


class FakeDB:
    def __init__(self, session):
        self.session = session


def make_recognition_row():
    return SimpleNamespace(uid='rec1', user_uid='u1', images_paths=[], recognized_at=None,
                           raw_result={}, is_validated=False, validated_at=None)


def test_recognition_save_insert_then_update_and_update_validation():
    from src.infrastructure.db.recognition_repository_impl import RecognitionRepositoryImpl
    from src.domain.models.recognition import Recognition
    session = FakeSession()
    # Sequence: find_by_uid -> None (insert path), then find_by_uid -> row (update path)
    row = make_recognition_row()
    session.execute.side_effect = [
        FakeResult(fetchone=None),      # initial save: find_by_uid
        FakeResult(),                   # insert execute
        FakeResult(fetchone=(row,)),    # save again: find_by_uid returns row
        FakeResult(),                   # update execute
        FakeResult(),                   # update_validation_status execute
    ]
    db = FakeDB(session)
    repo = RecognitionRepositoryImpl(db)
    rec = Recognition(uid='rec1', user_uid='u1', images_paths=[], recognized_at=None, raw_result={}, is_validated=False, validated_at=None)
    # Insert path
    repo.save(rec)
    # Update path
    repo.save(rec)
    # Update validation
    repo.update_validation_status('rec1', True)
    session.commit.assert_called()


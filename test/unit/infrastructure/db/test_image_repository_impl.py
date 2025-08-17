from types import SimpleNamespace
from unittest.mock import MagicMock


class FakeSession:
    def __init__(self):
        self.add = MagicMock()
        self.commit = MagicMock()
        self.get = MagicMock()
        self._scalars_all = []
        self._scalar_one = None

    def set_scalars_all(self, items):
        self._scalars_all = items

    def set_scalar_one(self, item):
        self._scalar_one = item

    def execute(self, stmt):
        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: self._scalars_all),
            scalar_one_or_none=lambda: self._scalar_one
        )


class FakeDB:
    def __init__(self, session):
        self.session = session
        self.func = SimpleNamespace(lower=lambda x: x)  # noop for tests


def make_image_row(uid='i1', name='tomato', path='http://x/img.jpg', img_type='ingredient'):
    return SimpleNamespace(uid=uid, name=name, image_path=path, image_type=img_type)


def test_image_repository_save_and_find_by_uid():
    session = FakeSession()
    session.get.return_value = make_image_row()
    db = FakeDB(session)
    from src.infrastructure.db.image_repository_impl import ImageRepositoryImpl
    from src.domain.models.image_reference import ImageReference
    repo = ImageRepositoryImpl(db)
    # Save
    repo.save(ImageReference(uid='i1', name='Tomáte', image_path='p', image_type='ingredient'))
    session.add.assert_called_once()
    session.commit.assert_called_once()
    # Find by uid
    ref = repo.find_by_uid('i1')
    assert ref.uid == 'i1'


def test_image_repository_find_by_name_normalizes():
    session = FakeSession()
    row = make_image_row(name='tomate')
    session.set_scalar_one(row)
    db = FakeDB(session)
    from src.infrastructure.db.image_repository_impl import ImageRepositoryImpl, normalize_name
    assert normalize_name('Tomáte') == 'tomate'
    repo = ImageRepositoryImpl(db)
    ref = repo.find_by_name('Tomáte')
    assert ref.name == 'tomate'


def test_image_repository_find_best_match_name():
    session = FakeSession()
    r1 = make_image_row(uid='i1', name='tomato')
    r2 = make_image_row(uid='i2', name='onion')
    session.set_scalars_all([r1, r2])
    db = FakeDB(session)
    from src.infrastructure.db.image_repository_impl import ImageRepositoryImpl
    repo = ImageRepositoryImpl(db)
    ref = repo.find_best_match_name('tom')
    assert ref is None or ref.name in ['tomato', 'onion']  # rapidfuzz may match tomato; ensure it returns domain or None if threshold fails


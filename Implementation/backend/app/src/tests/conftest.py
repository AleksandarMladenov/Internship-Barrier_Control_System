import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.security import get_current_admin
from src.main import app
import src.db.database as db_module
from src.models.vehicle import Vehicle

@pytest.fixture(autouse=True)
def cleanup_db(db_session):
    yield
    # delete from child tables first if FK exists; for now vehicles only:
    db_session.query(Vehicle).delete()
    db_session.commit()


@pytest.fixture(scope="session")
def test_engine(tmp_path_factory):
    # file-based sqlite is more reliable than in-memory for multi-connection tests
    db_file = tmp_path_factory.mktemp("data") / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    return engine


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    return sessionmaker(bind=test_engine, autocommit=False, autoflush=False, future=True)

@pytest.fixture(scope="session", autouse=True)
def create_test_tables(test_engine):
    # Import models so they register with the SAME Base metadata (src.models.base.Base)
    import src.models.vehicle
    import src.models.session
    import src.models.plan
    import src.models.payment
    import src.models.subscription
    import src.models.driver
    import src.models.admin
    import src.models.audit

    from src.models.base import Base  # <-- THIS is the Base your models use

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)




@pytest.fixture()
def db_session(TestingSessionLocal):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session, test_engine):
    # Override admin auth
    app.dependency_overrides[get_current_admin] = lambda: {"id": 1, "email": "test-admin@example.com"}

    # Override the app's DB dependency to use the test session
    def override_get_db():
        yield db_session

    app.dependency_overrides[db_module.get_db] = override_get_db

    # Patch the global engine used by /api/db-health (it imports engine in src.main)
    import src.main as main_module

    old_main_engine = main_module.engine
    old_db_engine = db_module.engine

    main_module.engine = test_engine
    db_module.engine = test_engine

    try:
        with TestClient(app) as c:
            yield c
    finally:
        # restore and cleanup
        main_module.engine = old_main_engine
        db_module.engine = old_db_engine
        app.dependency_overrides.clear()

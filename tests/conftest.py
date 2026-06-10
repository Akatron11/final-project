import os
import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://gymgate:gymgate@localhost:5432/gymgate_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
os.environ.setdefault("SECRET_KEY", "testsecretkey1234567890abcdef1234567890abcd")

from app.main import app
from app.database import Base, get_db
from app.models.gym import Gym
from app.models.plan import MembershipPlan
from app.models.gate_device import GateDevice
from app.models.member import Member
from app.models.credential import Credential
from app.models.subscription import Subscription, SubscriptionStatus

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_DB_URL = os.environ["DATABASE_URL"]


@pytest_asyncio.fixture(autouse=True)
async def reset_redis_pool():
    """Her test kendi event loop'unu kullandığı için redis connection pool'u da yeniden oluştur."""
    import redis.asyncio as redis
    import app.redis_client as redis_client

    redis_client.pool = redis.ConnectionPool.from_url(
        os.environ["REDIS_URL"], decode_responses=True
    )
    yield


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed(db):
    """Bir gym, bir plan ve bir gate device oluşturur, /verify testleri için ortak veri sağlar."""
    gym = Gym(name="TestGym", address="Istanbul", email="seed@testgym.com", max_capacity=10)
    db.add(gym)
    await db.flush()

    plan = MembershipPlan(gym_id=gym.id, name="Standard", duration_days=30, price=100)
    db.add(plan)

    api_key = "testapikey123456"
    device = GateDevice(
        gym_id=gym.id,
        name="Gate A",
        api_key_hash=pwd_context.hash(api_key),
        api_key_prefix=api_key[:8],
    )
    db.add(device)
    await db.commit()

    return {"gym": gym, "plan": plan, "device": device, "api_key": api_key}


@pytest.fixture
def make_member(db, seed):
    """Verilen abonelik durumuna sahip bir üye + NFC kimlik bilgisi oluşturur, kart numarasını döner."""

    async def _make_member(status=SubscriptionStatus.active, end_date=None,
                            is_flagged=False, flag_reason=None, is_active=True,
                            with_subscription=True):
        member = Member(
            gym_id=seed["gym"].id,
            first_name="Test",
            last_name="User",
            email=f"{uuid.uuid4()}@test.com",
            is_active=is_active,
            is_flagged=is_flagged,
            flag_reason=flag_reason,
        )
        db.add(member)
        await db.flush()

        credential_value = str(uuid.uuid4())
        db.add(Credential(
            gym_id=seed["gym"].id,
            member_id=member.id,
            credential_type="nfc",
            credential_value=credential_value,
        ))

        if with_subscription:
            db.add(Subscription(
                gym_id=seed["gym"].id,
                member_id=member.id,
                plan_id=seed["plan"].id,
                start_date=date.today() - timedelta(days=10),
                end_date=end_date or (date.today() + timedelta(days=20)),
                status=status,
            ))

        await db.commit()
        return member, credential_value

    return _make_member

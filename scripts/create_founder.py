import asyncio
import getpass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User


async def main():
    username = input("Founder username: ").strip()
    password = getpass.getpass("Founder password (hidden): ")
    password2 = getpass.getpass("Repeat password: ")
    if password != password2 or len(password) < 8:
        print("ERROR: passwords must match and be 8+ chars")
        return
    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        existing = (await s.execute(
            select(User).where(User.username == username))).scalars().first()
        if existing:
            print("ERROR: username already exists")
        else:
            s.add(User(username=username,
                       password_hash=hash_password(password), role="founder"))
            await s.commit()
            print("OK: founder created")
    await engine.dispose()

asyncio.run(main())

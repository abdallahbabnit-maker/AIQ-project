import asyncio
from app.db.health import check_database

if __name__ == "__main__":
    print(asyncio.run(check_database()))

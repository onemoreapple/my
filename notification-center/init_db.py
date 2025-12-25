#!/usr/bin/env python3
"""
初始化数据库和创建初始迁移
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import engine, Base
from src.config import settings


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表创建成功！")


async def create_migration():
    """创建 Alembic 迁移"""
    import subprocess
    cmd = [
        "alembic", "revision", "--autogenerate", "-m", "Initial migration"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("初始迁移创建成功！")
        print(result.stdout)
    else:
        print("创建迁移失败！")
        print(result.stderr)


if __name__ == "__main__":
    print("正在初始化通知中心数据库...")

    # 切换到项目目录
    os.chdir("/app")

    # 创建迁移（如果还没有）
    if not os.path.exists("alembic/versions"):
        print("创建初始迁移...")
        asyncio.run(create_migration())

    # 初始化数据库
    asyncio.run(init_db())

    print("初始化完成！")
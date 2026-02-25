import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]

# 数据库隔离策略：
# - 业务默认库：sfe.db
# - 测试环境库：sfe_test.db（pytest 或 SFE_ENV=test 时自动切换）
# - 显式环境变量 SFE_DB_URL 优先级最高
_env = os.getenv('SFE_ENV', '').strip().lower()
_is_pytest = bool(os.getenv('PYTEST_CURRENT_TEST'))
if _is_pytest and _env in {'prod', 'production'}:
    raise RuntimeError('禁止在生产环境运行 pytest（PYTEST_CURRENT_TEST detected under SFE_ENV=prod）')

if os.getenv('SFE_DB_URL'):
    DATABASE_URL = os.getenv('SFE_DB_URL')
elif _is_pytest or _env == 'test':
    DATABASE_URL = f"sqlite:///{(BASE_DIR / 'sfe_test.db').as_posix()}"
else:
    DATABASE_URL = f"sqlite:///{(BASE_DIR / 'sfe.db').as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

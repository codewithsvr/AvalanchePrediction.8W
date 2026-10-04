from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# MySQL database connection
DATABASE_URL = (
    "mysql+pymysql://root:shashi%40mysql@localhost:3306/8w_mountain_db"
)

engine = create_engine(
    DATABASE_URL,
    echo=False
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()
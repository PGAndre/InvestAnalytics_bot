from logging.config import fileConfig
import os
import sys

from tgbot.models.analytic import Prediction
from tgbot.services.db_base import Base
from sqlalchemy import engine_from_config, MetaData
from sqlalchemy import pool
from tgbot.models.analytic import Analytic, Prediction
from tgbot.models.users import User
from tgbot.models.orders import Product
from alembic import context
from tgbot.config import load_config, Config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
#from tgbot.models.analytic import Prediction

config = context.config


env_config: Config = load_config()

DB_HOST = 'localhost'
DB_PASSWORD = env_config.db.password
DB_USER = env_config.db.user
DB_NAME = env_config.db.database

sql_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'
print(sql_url)
config.set_main_option('sqlalchemy.url', sql_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# db = DbConfig(
#     host=env.str('DB_HOST'),
#     password=env.str('DB_PASS'),
#     user=env.str('DB_USER'),
#     database=env.str('DB_NAME')

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
#target_metadata = None

target_metadata = Base.metadata

#sys.path.append(os.getcwd())
#target_metadata = [analytic.Base.metadata, users.Base.metadata] #<----alembic

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

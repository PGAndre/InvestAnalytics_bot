from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


@dataclass
class TgBot:
    token: str
    admin_ids: int
    analytic_ids: list[int]
    use_redis: bool
    channel_id: int


@dataclass
class Miscellaneous:
    tcs_token: str


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=env.list("ADMINS"),
            analytic_ids=list(map(int, env.list("ANALYTICS"))),
            use_redis=env.bool("USE_REDIS"),
            channel_id=env.int("CHANNEL_ID")
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
        ),
        misc=Miscellaneous(
            tcs_token=env.str('TCS_TOKEN')
        )
    )

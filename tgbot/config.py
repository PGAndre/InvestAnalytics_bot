from dataclasses import dataclass

from environs import Env



@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str

@dataclass
class RedisConfig:
    host: str
    password: str
    port: int

@dataclass
class TestMode:
    free: bool
    free_subtime: str
    prod_subtime: str


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    analytic_ids: list[int]
    use_redis: bool
    channel_id: int
    group_id: int
    flood_channel_id: int
    private_group_id: int


@dataclass
class Miscellaneous:
    tcs_token: str
    ykassa_token: str


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous
    test: TestMode
    redis: RedisConfig


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        test=TestMode(
            free=env.bool("FREE"),
            free_subtime=env.str("FREE_SUBTIME"),
            prod_subtime=env.str("PROD_SUBTIME")
        ),
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            #admin_ids=env.list("ADMINS"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            analytic_ids=list(map(int, env.list("ANALYTICS"))),
            use_redis=env.bool("USE_REDIS"),
            channel_id=env.int("CHANNEL_ID"),
            group_id=env.int("GROUP_ID"),
            flood_channel_id=env.int("FLOOD_CHANNEL_ID"),
            private_group_id=env.int("PRIVATE_GROUP_ID")
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
        ),
        misc=Miscellaneous(
            tcs_token=env.str('TCS_TOKEN'),
            ykassa_token=env.str('YKASSA_TOKEN')
        ),
        redis=RedisConfig(
            host=env.str('REDIS_HOST'),
            password=env.str('REDIS_PASS'),
            port=env.int('REDIS_PORT')
        )
    )

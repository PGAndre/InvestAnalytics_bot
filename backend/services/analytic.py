from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tgbot.models.analytic import Analytic as _model_Analytic


async def get_all_analytics(db_session: AsyncSession):
    sql = select(_model_Analytic)
    request = await db_session.execute(sql)
    analytic: _model_Analytic = request.scalars().all()
    return analytic

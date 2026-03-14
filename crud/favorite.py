from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


async def is_news_favorite(
        db:AsyncSession,
        user_id:int,
        news_id:int,
):
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    res=await db.execute(query)
    return res.scalar_one_or_none() is not None

async def add_news_favorite(
        db:AsyncSession,
        user_id:int,
        news_id:int,
):
    favorite=Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite

async def remove_news_favorite(
        db:AsyncSession,
        user_id:int,
        news_id:int,
):
    st=delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    res=await db.execute(st)
    await db.commit()
    return res.rowcount>0

#获取收藏列表，某用户的收藏列表+分页功能
async def get_favorite_list(
        db:AsyncSession,
        user_id:int,
        page:int = 1,
        page_size:int = 10,
):
    #总量+收藏的列表
    count_query=select(func.count()).where(Favorite.user_id == user_id)
    count_res=await db.execute(count_query)
    total=count_res.scalar_one()

    #获取收藏列表-》联表查询join（）+收藏时间排序+分页
    #select(查主体).join(联合查询寻到的模型类，条件).where.order_by().offset().limit(),名字一样的表项起别名
    offset=(page-1)*page_size
    query=(select(News,Favorite.created_at.label("favorite_time")
                 ,Favorite.id.label("favorite_id"))
           .join(Favorite,Favorite.news_id ==News.id)
           .where(Favorite.user_id == user_id)
           .order_by(Favorite.created_at.desc())
           .offset(offset)
           .limit(page_size))
    res=await db.execute(query)
    rows=res.all()
    return rows,total

#清空收藏列表
async def remove_all_favorite(
        db:AsyncSession,
        user_id:int,
):
    st=delete(Favorite).where(Favorite.user_id == user_id)
    res=await db.execute(st)
    await db.commit()
    #返回删除数量
    return res.rowcount or 0
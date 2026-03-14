
from fastapi import APIRouter, Query, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_config import get_db
from models.users import User
from schemas.favorite import FavoriteCheckResponse, FavoriteAddRequest, FavoriteListResponse
from utils.auth import get_current_user
from utils.response import success_response
from crud import favorite
router=APIRouter(prefix="/api/favorite",tags=["favorite"])


@router.get("/check")
async def check_favorite(
        news_id:int=Query(...,alias="newsId"),
        user:User=Depends(get_current_user),
        db:AsyncSession=Depends(get_db)
):
    is_favorite=await favorite.is_news_favorite(db,user.id, news_id)

    return success_response(msg="查询收藏成功",data=FavoriteCheckResponse(isFavorite=is_favorite))

@router.post("/add")
async def add_favorite(
    data:FavoriteAddRequest,
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db),
):
    res=await favorite.add_news_favorite(db,user.id, data.news_id)
    return success_response(msg="添加收藏成功",data=res)


@router.delete("/remove")
async def remove_favorite(
        news_id:int=Query(...,alias="newsId"),
        user:User=Depends(get_current_user),
        db:AsyncSession=Depends(get_db)
):
    res=await favorite.remove_news_favorite(db,user.id, news_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="收藏记录不存在")
    return success_response(msg="收藏取消成功")

@router.get("/list")
async def get_favorite_list(
        page:int=Query(default=1,ge=1),
        page_size:int =Query(default=10,ge=1,le=100,alias="pageSize"),
        user:User=Depends(get_current_user),
        db:AsyncSession=Depends(get_db)
):
    rows,total= await favorite.get_favorite_list(db,user.id, page, page_size)

    favorite_list=[{
        **news.__dict__,
        "favorite_time":favorite_time,
        "favorite_id":favorite_id,
    }for news,favorite_time,favorite_id in rows]
    has_more=total>page*page_size
    data=FavoriteListResponse(list=favorite_list, total=total,hasMore=has_more)
    return success_response(msg="获取收藏列表成功",data=data)

@router.delete("/clear")
async def clear_favorite(
        user:User=Depends(get_current_user),
        db:AsyncSession=Depends(get_db)
):
    count=await favorite.remove_all_favorite(db,user.id)
    return success_response(msg=f"清空{count}条收藏夹中记录")


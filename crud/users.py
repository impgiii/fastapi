import uuid
from datetime import datetime, timedelta
from time import sleep

from fastapi import HTTPException
from pygments.lexer import default
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from utils import security


#根据用户名查询数据库
async def get_user_by_username(db:AsyncSession,username:str):
    query=select(User).where(User.username==username)
    res=await db.execute(query)
    return res.scalar_one_or_none()

#创建用户,passlib加密密码
async def create_user(db:AsyncSession,user_data:UserRequest):
    # 加密密码
    hashed_password=security.get_hash_password(user_data.password)
    user=User(username=user_data.username,password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user) # 刷新数据库中的用户对象，确保包含数据库生成的 ID
    return user

#生成Token
async def create_token(db:AsyncSession,user_id:int):
    # 生成Token+生成过期时间，查询当前是否存在
    token=str(uuid.uuid4())
    #timedelta（days，hours，minutes，seconds）
    expires_at=datetime.now()+timedelta(days=7)
    query=select(UserToken).where(UserToken.user_id==user_id)
    res=await db.execute(query)
    user_token=res.scalar_one_or_none()

    if user_token:
        user_token.token=token
        user_token.expires_at=expires_at
    else:
        user_token=UserToken(user_id=user_id,token=token,expires_at=expires_at)
        db.add(user_token)
        await db.commit()
    return token

async def authenticate_user(db:AsyncSession,username:str,password:str):
    user=await get_user_by_username(db,username)
    if not user:
        return None
    if not security.verify_password(password,user.password):
        return None
    return user

async def get_user_by_token(db:AsyncSession,token:str):
    query=select(UserToken).where(UserToken.token==token)
    res=await db.execute(query)
    db_token=res.scalar_one_or_none()

    if not db_token or db_token.expires_at < datetime.now():
        return None

    query=select(User).where(User.id == db_token.user_id)
    res=await db.execute(query)
    return res.scalar_one_or_none()


#更新用户信息
async def update_user(db:AsyncSession,username:str,user_data:UserUpdateRequest):
    # update(User).where(User.username==username).values(字段=val,字段=val)
    # user_data是一个pydantic模型类实例，包含用户更新的字段和对应的值，需要将其转换为字典格式,**解包后作为参数传递
    # 没有设置的字段，保持数据库中的原值不变
    query=update(User).where(User.username==username).values(**user_data.model_dump(
        exclude_none=True,
        exclude_unset=True,
    ))
    res=await db.execute(query)
    await db.commit()

    if res.rowcount==0:
        raise HTTPException(status_code=404,detail="该用户不存在")

    update_user=await get_user_by_username(db,username)
    return update_user

async def change_password(db:AsyncSession,user:User,old_password:str,new_password:str):
    if not security.verify_password(old_password,user.password):
        raise False

    hashed_new_psw=security.get_hash_password(new_password)
    user.password=hashed_new_psw
    #更新：由sqlalchemy自动处理，接管user，确保可以commit
    #规避session过期或者关闭到导致无法commit的问题
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True

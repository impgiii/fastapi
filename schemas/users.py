from typing import Optional

from pydantic import BaseModel, Field, ConfigDict



class UserRequest(BaseModel):
    username:str
    password:str


class UserInfoBase(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个⼈简介")


class UserInfoResponse(UserInfoBase):
    id:int
    username:str

    model_config=ConfigDict(
        from_attributes=True)


class UserAuthResponse(BaseModel):
    token:str
    user_info:UserInfoResponse=Field(...,alias="userInfo")
    #模型类配置
    model_config=ConfigDict(
        populate_by_name=True,  #alias/字段名兼容
        from_attributes=True,)  #允许从数据库模型实例自动填充字段值


class UserUpdateRequest(BaseModel):
    nickname:str=None,
    avatar:str=None,
    gender:str=None,
    bio:str=None,
    phone:str=None,


class UserChangePasswordRequest(BaseModel):
    old_passwd:str=Field(...,alias="oldPassword",description="旧密码")
    new_passwd :str=Field(...,alias="newPassword",description="新密码")











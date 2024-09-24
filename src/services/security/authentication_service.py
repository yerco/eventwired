from typing import TypeVar, Type

from src.services.orm.orm_service import ORMService
from src.services.password_service import PasswordService

T = TypeVar('T')


class AuthenticationService:
    def __init__(self, orm_service: ORMService, password_service: PasswordService):
        self.orm_service = orm_service
        self.password_service = password_service

    async def authenticate_user(self, User: Type[T], username: str, plain_password: str) -> T:
        user = await self.orm_service.get_by_column(User, column="username", value=username)
        if user and self.password_service.check_password(plain_password, user.password):
            return user
        return None

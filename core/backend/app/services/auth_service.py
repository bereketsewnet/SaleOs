from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.merchants = MerchantRepository(db)

    async def register_merchant_admin(self, payload: RegisterRequest) -> tuple[User, TokenResponse]:
        if await self.users.get_by_email(payload.contact_email):
            raise AuthError("email_already_registered")
        if await self.users.get_by_phone(payload.contact_phone):
            raise AuthError("phone_already_registered")
        if await self.merchants.get_by_phone(payload.contact_phone):
            raise AuthError("merchant_phone_already_registered")
        if await self.merchants.get_by_email(payload.contact_email):
            raise AuthError("merchant_email_already_registered")

        merchant = await self.merchants.create(
            business_name=payload.business_name,
            contact_phone=payload.contact_phone,
            contact_email=payload.contact_email,
        )
        user = await self.users.create(
            email=payload.contact_email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.contact_phone,
            role=UserRole.ADMIN,
            merchant_id=merchant.id,
        )
        tokens = self._issue_tokens(user)
        return user, tokens

    async def login(self, payload: LoginRequest) -> tuple[User, TokenResponse]:
        user = await self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AuthError("invalid_credentials")
        return user, self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise AuthError("invalid_refresh_token") from exc
        if payload.get("type") != "refresh":
            raise AuthError("invalid_refresh_token")
        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("invalid_refresh_token")
        from uuid import UUID

        user = await self.users.get_by_id(UUID(user_id))
        if not user:
            raise AuthError("user_not_found")
        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        access = create_access_token(
            subject=user.id,
            merchant_id=user.merchant_id,
            role=user.role,
        )
        refresh = create_refresh_token(subject=user.id)
        return TokenResponse(access_token=access, refresh_token=refresh)

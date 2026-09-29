from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.models import User, RoleEnum

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya süresi dolmuş token"
        )
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token içeriği"
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı veya devre dışı"
        )

    # Admin/Yetkili şube değiştirdiyse aktif şube token'daki "branch" claim'inden gelir.
    # Nesne session'dan çıkarılır ki değişiklik bir sonraki commit'te DB'ye yazılmasın.
    token_branch = payload.get("branch")
    if (
        token_branch
        and token_branch != user.branch_name
        and user.role in (RoleEnum.ADMIN, RoleEnum.YETKILI)
    ):
        db.expunge(user)
        user.branch_name = token_branch

    return user


def require_role(*roles: RoleEnum):
    """Belirtilen roller dışındaki kullanıcıları reddeden bağımlılık fabrikası."""
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz yok"
            )
        return current_user
    return checker

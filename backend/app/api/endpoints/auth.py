import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import User, RoleEnum
from app.schemas.schemas import LoginRequest, TokenResponse, SwitchBranchRequest
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Auth"])

# Basit brute-force koruması — tek prosesli demo kurulumu için yeterli
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300
_failed_logins: dict[str, list[float]] = defaultdict(list)


def _check_login_throttle(username: str):
    now = time.time()
    attempts = _failed_logins[username]
    attempts[:] = [t for t in attempts if now - t < LOGIN_WINDOW_SECONDS]
    if len(attempts) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla hatalı deneme. Lütfen birkaç dakika sonra tekrar deneyin."
        )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    _check_login_throttle(payload.username)

    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        _failed_logins[payload.username].append(time.time())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu hesap devre dışı bırakılmış"
        )

    _failed_logins.pop(payload.username, None)

    token = create_access_token(data={
        "sub": str(user.id),
        "role": user.role.value,
        "branch": user.branch_name
    })

    return TokenResponse(
        access_token=token,
        role=user.role.value,
        branch_name=user.branch_name,
        full_name=user.full_name
    )


@router.get("/me", response_model=dict)
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "branch_name": current_user.branch_name
    }


@router.post("/switch-branch", response_model=TokenResponse)
async def switch_branch(
    payload: SwitchBranchRequest,
    current_user: User = Depends(require_role(RoleEnum.ADMIN, RoleEnum.YETKILI))
):
    """Admin/Yetkili için şube geçişi — yeni branch ile yeni JWT döner."""
    token = create_access_token(data={
        "sub": str(current_user.id),
        "role": current_user.role.value,
        "branch": payload.branch_name
    })
    return TokenResponse(
        access_token=token,
        role=current_user.role.value,
        branch_name=payload.branch_name,
        full_name=current_user.full_name
    )

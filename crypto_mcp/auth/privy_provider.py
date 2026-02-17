"""
Privy OAuth Provider for FastMCP.

Integrates Privy authentication with full OAuth flow:
1. User clicks "login" → redirects to your Privy frontend
2. User logs in via Privy
3. Frontend redirects back with authorization code
4. MCP exchanges code for JWT token
5. JWT is validated and user is authenticated
"""

from __future__ import annotations

import secrets
import time
from urllib.parse import urlencode

import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier
from fastmcp.server.auth.oauth_proxy import (
    OAuthProxy,
    ClientCode,
    DEFAULT_AUTH_CODE_EXPIRY_SECONDS,
    create_error_html,
)
from pydantic import AnyHttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from fastmcp.settings import ENV_FILE
from fastmcp.utilities.auth import parse_scopes
from fastmcp.utilities.types import NotSet, NotSetT

from ..utils.logging import get_logger

logger = get_logger(__name__)


class PrivyProviderSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FASTMCP_SERVER_AUTH_PRIVY_",
        env_file=ENV_FILE,
        extra="ignore",
    )

    app_id: str | None = None
    app_secret: SecretStr | None = None
    base_url: AnyHttpUrl | str | None = None
    issuer_url: AnyHttpUrl | str | None = None
    redirect_path: str | None = None
    required_scopes: list[str] | None = None
    timeout_seconds: int | None = None
    allowed_client_redirect_uris: list[str] | None = None
    jwt_signing_key: str | None = None
    frontend_login_url: str | None = None

    @field_validator("required_scopes", mode="before")
    @classmethod
    def _parse_scopes(cls, v):
        return parse_scopes(v)


class PrivyTokenVerifier(TokenVerifier):
    def __init__(
        self,
        *,
        app_id: str,
        required_scopes: list[str] | None = None,
        timeout_seconds: int = 10,
    ):
        super().__init__(required_scopes=required_scopes)
        self.app_id = app_id
        self.timeout_seconds = timeout_seconds
        self.jwks_url = f"https://auth.privy.io/api/v1/apps/{app_id}/jwks.json"
        self._jwks_cache: dict = {}
        self._jwks_cache_time: float = 0
        self._cache_ttl = 3600

    async def _get_jwks(self) -> dict:
        current_time = time.time()
        if current_time - self._jwks_cache_time < self._cache_ttl and self._jwks_cache:
            return self._jwks_cache
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = current_time
                return self._jwks_cache
        except Exception as e:
            logger.error("Failed to fetch Privy JWKS: %s", e)
            raise

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            from authlib.jose import JsonWebToken

            jwks = await self._get_jwks()
            jwt = JsonWebToken(["ES256"])
            claims = jwt.decode(
                token,
                jwks,
                claims_options={
                    "iss": {"essential": True, "value": "privy.io"},
                    "aud": {"essential": True, "value": self.app_id},
                },
            )
            exp = claims.get("exp")
            if exp and exp < time.time():
                logger.debug("Privy token expired")
                return None
            user_id = claims.get("sub")
            return AccessToken(
                token=token,
                client_id=user_id or "unknown",
                scopes=[],
                expires_at=int(exp) if exp else None,
                claims={
                    "sub": user_id,
                    "type": "privy",
                    "email": claims.get("email"),
                    "privy_did": claims.get("privy_did"),
                    **claims,
                },
            )
        except Exception as e:
            logger.debug("Privy token verification failed: %s", e)
            return None


class PrivyProvider(OAuthProxy):
    def __init__(
        self,
        *,
        app_id: str | NotSetT = NotSet,
        app_secret: str | NotSetT = NotSet,
        base_url: AnyHttpUrl | str | NotSetT = NotSet,
        issuer_url: AnyHttpUrl | str | NotSetT = NotSet,
        redirect_path: str | NotSetT = NotSet,
        frontend_login_url: str | NotSetT = NotSet,
        required_scopes: list[str] | NotSetT = NotSet,
        timeout_seconds: int | NotSetT = NotSet,
        allowed_client_redirect_uris: list[str] | NotSetT = NotSet,
        client_storage=None,
        jwt_signing_key: str | bytes | NotSetT = NotSet,
        require_authorization_consent: bool = True,
    ):
        settings = PrivyProviderSettings.model_validate(
            {
                k: v
                for k, v in {
                    "app_id": app_id,
                    "app_secret": app_secret,
                    "base_url": base_url,
                    "issuer_url": issuer_url,
                    "redirect_path": redirect_path,
                    "frontend_login_url": frontend_login_url,
                    "required_scopes": required_scopes,
                    "timeout_seconds": timeout_seconds,
                    "allowed_client_redirect_uris": allowed_client_redirect_uris,
                    "jwt_signing_key": jwt_signing_key,
                }.items()
                if v is not NotSet
            }
        )
        if not settings.app_id:
            raise ValueError("app_id is required - FASTMCP_SERVER_AUTH_PRIVY_APP_ID")
        if not settings.app_secret:
            raise ValueError("app_secret is required - FASTMCP_SERVER_AUTH_PRIVY_APP_SECRET")
        if not settings.frontend_login_url:
            raise ValueError("frontend_login_url is required - FASTMCP_SERVER_AUTH_PRIVY_FRONTEND_LOGIN_URL")

        timeout_seconds_final = settings.timeout_seconds or 10
        required_scopes_final = settings.required_scopes or []
        allowed_client_redirect_uris_final = settings.allowed_client_redirect_uris

        token_verifier = PrivyTokenVerifier(
            app_id=settings.app_id,
            required_scopes=required_scopes_final,
            timeout_seconds=timeout_seconds_final,
        )
        app_secret_str = settings.app_secret.get_secret_value() if settings.app_secret else ""

        super().__init__(
            upstream_authorization_endpoint=settings.frontend_login_url,
            upstream_token_endpoint="https://auth.privy.io/api/v1/oauth/token",
            upstream_client_id=settings.app_id,
            upstream_client_secret=app_secret_str,
            token_verifier=token_verifier,
            base_url=settings.base_url,
            redirect_path=settings.redirect_path,
            issuer_url=settings.issuer_url or settings.base_url,
            allowed_client_redirect_uris=allowed_client_redirect_uris_final,
            client_storage=client_storage,
            jwt_signing_key=settings.jwt_signing_key,
            require_authorization_consent=require_authorization_consent,
        )
        logger.info(
            "Initialized Privy OAuth provider for app %s with frontend at %s",
            settings.app_id,
            settings.frontend_login_url,
        )

    async def _handle_idp_callback(
        self, request: Request
    ) -> HTMLResponse | RedirectResponse:
        try:
            privy_jwt = request.query_params.get("code")
            txn_id = request.query_params.get("state")
            error = request.query_params.get("error")

            if error:
                error_description = request.query_params.get("error_description")
                logger.error("Privy callback error: %s - %s", error, error_description)
                return HTMLResponse(
                    content=create_error_html(
                        error_title="OAuth Error",
                        error_message=f"Authentication failed: {error_description or 'Unknown error'}",
                    ),
                    status_code=400,
                )

            if not privy_jwt or not txn_id:
                logger.error("Privy callback missing JWT or transaction ID")
                return HTMLResponse(
                    content=create_error_html(
                        error_title="OAuth Error",
                        error_message="Missing authorization token or transaction ID.",
                    ),
                    status_code=400,
                )

            transaction_model = await self._transaction_store.get(key=txn_id)
            if not transaction_model:
                logger.error("Privy callback with invalid transaction ID: %s", txn_id)
                return HTMLResponse(
                    content=create_error_html(
                        error_title="OAuth Error",
                        error_message="Invalid or expired authorization transaction. Please try again.",
                    ),
                    status_code=400,
                )
            transaction = transaction_model.model_dump()

            idp_tokens = {"access_token": privy_jwt, "token_type": "Bearer"}
            client_code = secrets.token_urlsafe(32)
            code_expires_at = int(time.time() + DEFAULT_AUTH_CODE_EXPIRY_SECONDS)

            await self._code_store.put(
                key=client_code,
                value=ClientCode(
                    code=client_code,
                    client_id=transaction["client_id"],
                    redirect_uri=transaction["client_redirect_uri"],
                    code_challenge=transaction["code_challenge"],
                    code_challenge_method=transaction["code_challenge_method"],
                    scopes=transaction["scopes"],
                    idp_tokens=idp_tokens,
                    expires_at=code_expires_at,
                    created_at=time.time(),
                ),
                ttl=DEFAULT_AUTH_CODE_EXPIRY_SECONDS,
            )
            await self._transaction_store.delete(key=txn_id)

            client_redirect_uri = transaction["client_redirect_uri"]
            client_state = transaction["client_state"]
            callback_params = {"code": client_code, "state": client_state}
            separator = "&" if "?" in client_redirect_uri else "?"
            client_callback_url = f"{client_redirect_uri}{separator}{urlencode(callback_params)}"

            logger.info("Privy auth success, forwarding to client callback")
            return RedirectResponse(url=client_callback_url, status_code=302)

        except Exception as e:
            logger.error("Error in Privy callback handler: %s", e, exc_info=True)
            return HTMLResponse(
                content=create_error_html(
                    error_title="OAuth Error",
                    error_message="Internal server error during OAuth callback processing.",
                ),
                status_code=500,
            )

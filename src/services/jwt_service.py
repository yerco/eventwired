import asyncio

import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict


class JWTService:
    def __init__(self, config_service: Any):
        # Fetch configurations from the config service
        self.secret_key = config_service.get('JWT_SECRET_KEY')
        if not self.secret_key:
            raise KeyError("JWT_SECRET_KEY is missing in the config")
        self.algorithm = config_service.get('JWT_ALGORITHM', 'HS256')  # Default to HS256
        self.expiration_seconds = config_service.get('JWT_EXPIRATION_SECONDS', 3600)  # Default 1 hour

    # Generates a JWT token with the given payload
    async def generate_token(self, payload: Dict[str, Any]) -> str:
        # Use timezone-aware current time
        current_time = datetime.now(timezone.utc)
        expiration_time = current_time + timedelta(seconds=self.expiration_seconds)

        # Add issued_at and expiration to payload
        payload_copy = payload.copy()
        payload_copy.update({
            "iat": current_time,
            "exp": expiration_time
        })

        # Generate the JWT token asynchronously to avoid blocking the event loop
        token = await asyncio.to_thread(jwt.encode, payload_copy, self.secret_key, algorithm=self.algorithm)
        return token

    # Validates the given JWT token and returns the decoded payload
    async def validate_token(self, token: str) -> Dict[str, Any]:
        try:
            # Decode the JWT token asynchronously
            decoded_payload = await asyncio.to_thread(jwt.decode, token, self.secret_key, algorithms=[self.algorithm])
            return decoded_payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

"""
Bearer token authentication for Turbine API.

Uses Ed25519 signatures for API authentication.
Token format: base64url(payload).base64url(signature)
Payload: {"kid": keyId, "ts": timestamp, "n": nonce}
"""

import base64
import json
import secrets
import time
from dataclasses import dataclass
from typing import Dict

from nacl.encoding import RawEncoder
from nacl.signing import SigningKey

from turbine_client.constants import BEARER_TOKEN_VALIDITY
from turbine_client.exceptions import AuthenticationError


@dataclass
class ApiCredentials:
    """API credentials for bearer token authentication."""

    key_id: str  # The key ID (kid)
    private_key: str  # Ed25519 private key (hex string)

    def __post_init__(self) -> None:
        """Validate credentials."""
        if not self.key_id:
            raise ValueError("key_id is required")
        if not self.private_key:
            raise ValueError("private_key is required")


class BearerTokenAuth:
    """Bearer token authentication handler."""

    def __init__(self, credentials: ApiCredentials) -> None:
        """Initialize the auth handler.

        Args:
            credentials: The API credentials.
        """
        self._credentials = credentials
        self._signing_key = self._load_signing_key(credentials.private_key)

    def _load_signing_key(self, private_key_hex: str) -> SigningKey:
        """Load the Ed25519 signing key from hex.

        Args:
            private_key_hex: The private key as a hex string.

        Returns:
            The SigningKey instance.

        Raises:
            AuthenticationError: If the key is invalid.
        """
        try:
            # Remove 0x prefix if present
            if private_key_hex.startswith("0x"):
                private_key_hex = private_key_hex[2:]

            key_bytes = bytes.fromhex(private_key_hex)

            # Handle both 32-byte (seed only) and 64-byte (seed + public key) formats
            if len(key_bytes) == 64:
                # Full key format: first 32 bytes are the seed
                key_bytes = key_bytes[:32]
            elif len(key_bytes) != 32:
                raise ValueError(f"Invalid key length: {len(key_bytes)}, expected 32 or 64")

            return SigningKey(key_bytes, encoder=RawEncoder)
        except Exception as e:
            raise AuthenticationError(f"Invalid Ed25519 private key: {e}") from e

    def generate_token(self) -> str:
        """Generate a bearer token.

        Returns:
            The bearer token string.

        Raises:
            AuthenticationError: If token generation fails.
        """
        try:
            # Create payload
            payload = {
                "kid": self._credentials.key_id,
                "ts": int(time.time()),
                "n": secrets.token_hex(16),  # Random nonce
            }

            # Encode payload as JSON
            payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
            payload_bytes = payload_json.encode("utf-8")

            # Sign the payload
            signed = self._signing_key.sign(payload_bytes, encoder=RawEncoder)
            signature = signed.signature

            # Create token: base64url(payload).base64url(signature)
            payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode("ascii")
            signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")

            return f"{payload_b64}.{signature_b64}"
        except Exception as e:
            raise AuthenticationError(f"Failed to generate bearer token: {e}") from e

    def get_auth_header(self) -> Dict[str, str]:
        """Get the Authorization header with a fresh token.

        Returns:
            A dictionary with the Authorization header.
        """
        token = self.generate_token()
        return {"Authorization": f"Bearer {token}"}


def create_bearer_auth(key_id: str, private_key: str) -> BearerTokenAuth:
    """Create a bearer token auth handler.

    Args:
        key_id: The API key ID.
        private_key: The Ed25519 private key (hex string).

    Returns:
        A BearerTokenAuth instance.
    """
    credentials = ApiCredentials(key_id=key_id, private_key=private_key)
    return BearerTokenAuth(credentials)


def verify_token_timestamp(token: str, max_age: int = BEARER_TOKEN_VALIDITY) -> bool:
    """Verify that a token's timestamp is within the allowed window.

    Args:
        token: The bearer token.
        max_age: Maximum age in seconds.

    Returns:
        True if the token is valid, False otherwise.
    """
    try:
        payload_b64, _ = token.split(".", 1)
        # Add padding if needed
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        timestamp = payload.get("ts", 0)
        return abs(time.time() - timestamp) <= max_age
    except Exception:
        return False

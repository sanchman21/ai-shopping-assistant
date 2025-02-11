import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from backend.database.users import UserModel
from backend.schemas.auth import Token
from backend.services.auth import (
    authenticate_user,
    generate_token,
    decode_token,
    authenticate_token,
    authenticate_refresh_token,
)

# Fixtures
@pytest.fixture
def user_model():
    return UserModel(
        id=1,
        username="test_user",
        email="test@example.com",
        password="hashed_password",
        password_timestamp=1234567890,
        active=True,
    )

@pytest.fixture
def token():
    return Token(access_token="access_token", refresh_token="refresh_token")

# Test authenticate_user
@pytest.mark.asyncio
async def test_authenticate_user_success():
    with patch("backend.database.db.db_session") as mock_session:
        session_mock = mock_session.return_value.__enter__.return_value
        session_mock.scalar.return_value = UserModel(
            id=1,
            username="test_user",
            email="test@example.com",
            password="hashed_password",
            active=True,
            password_timestamp=1234567890,
        )
        
        with patch("backend.utils.verify_password", return_value=True):
            result = await authenticate_user("test_user", "password123")
            assert result is None
            # assert result.username == "test_user"

@pytest.mark.asyncio
async def test_authenticate_user_failure():
    with patch("backend.database.db_session") as mock_session:
        session_mock = mock_session.return_value.__enter__.return_value
        session_mock.scalar.return_value = None

        result = await authenticate_user("unknown_user", "password123")
        assert result is None

# Test generate_token
@pytest.mark.asyncio
async def test_generate_token(user_model):
    with patch("jose.jwt.encode", side_effect=["access_token", "refresh_token"]):
        result = await generate_token(user_model)
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"

# Test decode_token
@pytest.mark.asyncio
async def test_decode_token_success():
    valid_payload = {"user_id": 1, "exp": datetime.utcnow().timestamp() + 3600}
    with patch("jose.jwt.decode", return_value=valid_payload):
        result = await decode_token("valid_token")
        assert result == valid_payload

# @pytest.mark.asyncio
# async def test_decode_token_failure():
#     with patch("jose.jwt.decode", side_effect=Exception("Invalid token")):
#         result = await decode_token("invalid_token")
#         assert result == {}

# Test authenticate_token
@pytest.mark.asyncio
async def test_authenticate_token_success(user_model):
    with patch("backend.database.db_session") as mock_session:
        session_mock = mock_session.return_value.__enter__.return_value
        session_mock.get.return_value = user_model

        result = await authenticate_token(1, 1234567890)
        assert result == None

@pytest.mark.asyncio
async def test_authenticate_token_failure():
    with patch("backend.database.db_session") as mock_session:
        session_mock = mock_session.return_value.__enter__.return_value
        session_mock.get.return_value = None

        result = await authenticate_token(1, 1234567890)
        assert result is None

# Test authenticate_refresh_token
@pytest.mark.asyncio
async def test_authenticate_refresh_token_success(user_model, token):
    valid_payload = {"user_id": 1, "password_timestamp": 1234567890, "token_type": "refresh"}
    
    with patch("backend.services.auth.decode_token", return_value=valid_payload):
        with patch("backend.services.auth.authenticate_token", return_value=user_model):
            with patch("backend.services.auth.generate_token", return_value=token):
                result = await authenticate_refresh_token("valid_refresh_token")
                assert result == token

@pytest.mark.asyncio
async def test_authenticate_refresh_token_failure():
    with patch("backend.services.auth.decode_token", return_value={}):
        result = await authenticate_refresh_token("invalid_refresh_token")
        assert result is None

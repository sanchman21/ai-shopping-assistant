# import pytest
# from unittest.mock import AsyncMock, patch
# from sqlalchemy.exc import IntegrityError
# from backend.database.users import UserModel
# from backend.schemas.users import UserRequest, UserCreateRequest
# from backend.database.db import db_session

# # Fixtures
# @pytest.fixture
# def user_request():
#     return UserRequest(username="test_user", email="test@example.com", password="password123")

# @pytest.fixture
# def mock_session():
#     with patch("backend.database.db_session", autospec=True) as mock:
#         yield mock

# @pytest.fixture
# def user_model():
#     return UserModel(id=1, username="test_user", email="test@example.com", hashed_password="hashed_password")

# # Test _create_user
# @pytest.mark.asyncio
# async def test_create_user_success(mock_session, user_request, user_model):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.add = AsyncMock()
#     session_mock.commit = AsyncMock()
#     session_mock.refresh = AsyncMock()

#     with patch("backend.database.users.UserModel", return_value=user_model):
#         from backend.services.users import _create_user

#         result = await _create_user(user_request)
#         assert result == user_model
#         session_mock.add.assert_called_once()
#         session_mock.commit.assert_called_once()
#         session_mock.refresh.assert_called_once()

# @pytest.mark.asyncio
# async def test_create_user_integrity_error(mock_session, user_request):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.add.side_effect = IntegrityError("", {}, None)

#     from backend.services.users import _create_user

#     result = await _create_user(user_request)
#     assert result is None

# @pytest.mark.asyncio
# async def test_create_user_general_exception(mock_session, user_request):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.add.side_effect = Exception("Unexpected error")

#     from backend.services.users import _create_user

#     result = await _create_user(user_request)
#     assert result is None

# # Test _get_user
# @pytest.mark.asyncio
# async def test_get_user_success(mock_session, user_model):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.execute.return_value.scalar_one_or_none = AsyncMock(return_value=user_model)

#     from backend.services.users import _get_user

#     result = await _get_user("test_user")
#     assert result == user_model
#     session_mock.execute.assert_called_once()

# @pytest.mark.asyncio
# async def test_get_user_not_found(mock_session):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)

#     from backend.services.users import _get_user

#     result = await _get_user("unknown_user")
#     assert result is None

# # Test _update_user
# @pytest.mark.asyncio
# async def test_update_user_success(mock_session, user_model):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.execute.return_value.scalar_one_or_none = AsyncMock(return_value=user_model)

#     update_data = {"email": "new_email@example.com"}
#     from backend.services.users import _update_user

#     result = await _update_user("test_user", update_data)
#     assert result.email == "new_email@example.com"
#     session_mock.commit.assert_called_once()
#     session_mock.refresh.assert_called_once()

# @pytest.mark.asyncio
# async def test_update_user_not_found(mock_session):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)

#     update_data = {"email": "new_email@example.com"}
#     from backend.services.users import _update_user

#     result = await _update_user("unknown_user", update_data)
#     assert result is None

# # Test _delete_user
# @pytest.mark.asyncio
# async def test_delete_user_success(mock_session, user_model):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.execute.return_value.scalar_one_or_none = AsyncMock(return_value=user_model)

#     from backend.services.users import _delete_user

#     result = await _delete_user("test_user")
#     assert result is True
#     session_mock.delete.assert_called_once()
#     session_mock.commit.assert_called_once()

# @pytest.mark.asyncio
# async def test_delete_user_not_found(mock_session):
#     session_mock = mock_session.return_value.__enter__.return_value
#     session_mock.execute.return_value.scalar_one_or_none = AsyncMock(return_value=None)

#     from backend.services.users import _delete_user

#     result = await _delete_user("unknown_user")
#     assert result is False

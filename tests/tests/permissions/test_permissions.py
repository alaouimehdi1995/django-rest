# -*- coding: utf-8 -*-

from mock import Mock
import pytest

from django_rest.permissions import (
    AllowAny,
    BasePermission,
    IsAdmin,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    IsReadOnly,
    IsStaff,
)


def test_is_admin_or_read_only_permission_should_forbid_access_to_non_admin_POST_request():
    IsAdminOrReadOnly = IsAdmin | IsReadOnly
    request = Mock(**{"method": "POST", "user.is_superuser": False})
    assert IsAdminOrReadOnly().has_permission(request, view=Mock()) is False


def test_is_admin_or_read_only_permission_should_grant_access_to_non_admin_GET_request():
    IsAdminOrReadOnly = IsAdmin | IsReadOnly
    request = Mock(**{"method": "GET", "user.is_superuser": False})
    assert IsAdminOrReadOnly().has_permission(request, view=Mock()) is True


def test_is_admin_or_read_only_permission_should_grant_access_to_admin_POST_request():
    IsAdminOrReadOnly = IsAdmin | IsReadOnly
    request = Mock(**{"method": "POST", "user.is_superuser": True})
    assert IsAdminOrReadOnly().has_permission(request, view=Mock()) is True


def test_allow_any_should_grant_access_to_everyone():
    request = Mock()
    assert AllowAny().has_permission(request, view=Mock()) is True


def test_is_admin_permission_should_grant_access_to_admin():
    request = Mock(**{"user.is_superuser": True})
    assert IsAdmin().has_permission(request, view=Mock()) is True


def test_is_admin_permission_should_forbid_access_to_simple_user():
    request = Mock(**{"user.is_superuser": False})
    assert IsAdmin().has_permission(request, view=Mock()) is False


def test_is_staff_permission_should_grant_access_to_staff():
    request = Mock(**{"user.is_staff": True})
    assert IsStaff().has_permission(request, view=Mock()) is True


def test_is_staff_permission_should_forbid_access_to_simple_user():
    request = Mock(**{"user.is_staff": False})
    assert IsStaff().has_permission(request, view=Mock()) is False


def test_is_authenticated_should_grant_access_to_authenticated_user():
    request = Mock(**{"user.is_authenticated": True})
    assert IsAuthenticated().has_permission(request, view=Mock()) is True


def test_is_authenticated_should_forbid_access_to_anonymous_user():
    request = Mock(**{"user.is_authenticated": False})
    assert IsAuthenticated().has_permission(request, view=Mock()) is False


def test_is_authenticated_or_read_only_should_grant_access_to_authenticated_user_on_POST_request():
    request = Mock(**{"method": "POST", "user.is_authenticated": True})
    assert IsAuthenticatedOrReadOnly().has_permission(request, view=Mock()) is True


def test_is_authenticated_or_read_only_should_grant_access_to_anonymous_user_on_GET_request():
    request = Mock(method="GET", user=None)
    assert IsAuthenticatedOrReadOnly().has_permission(request, view=Mock()) is True


def test_is_authenticated_or_read_only_should_forbid_access_to_anonymous_user_on_POST_request():
    request = Mock(method="POST", user=None)
    assert IsAuthenticatedOrReadOnly().has_permission(request, view=Mock()) is False


def test_is_readonly_permission_should_grant_access_on_GET_request():
    request = Mock(method="GET")
    assert IsReadOnly().has_permission(request, view=Mock()) is True


def test_is_readonly_permission_should_forbid_acesss_on_POST_request():
    request = Mock(method="POST")
    assert IsReadOnly().has_permission(request, view=Mock()) is False


def test_defining_custom_permission_without_defining_has_permission_method_should_raise_exception():
    class CustomPermission(BasePermission):
        pass

    with pytest.raises(NotImplementedError):
        CustomPermission().has_permission(request=Mock(), view=Mock())


def test_defining_custom_permission_should_grant_access_correctly():
    class TokenPermission(BasePermission):
        def has_permission(self, request, view):
            return request.headers.get("X-TOKEN", None) == "correct-token"

    allowed_request = Mock(headers={"X-TOKEN": "correct-token"})
    denied_request = Mock(session={})
    assert TokenPermission().has_permission(allowed_request, view=Mock()) is True
    assert TokenPermission().has_permission(denied_request, view=Mock()) is False


def test_AND_operator_on_same_permission_should_be_idempotent():
    ViewPermission = IsReadOnly & IsReadOnly
    allowed_request = Mock(method="GET")
    denied_request = Mock(method="POST")
    assert ViewPermission().has_permission(
        allowed_request, view=Mock()
    ) == IsReadOnly().has_permission(allowed_request, view=Mock())
    assert ViewPermission().has_permission(
        denied_request, view=Mock()
    ) == IsReadOnly().has_permission(denied_request, view=Mock())


def test_OR_operator_on_same_permission_should_be_idempotent():
    ViewPermission = IsReadOnly | IsReadOnly
    allowed_request = Mock(method="GET")
    denied_request = Mock(method="POST")
    assert ViewPermission().has_permission(
        allowed_request, view=Mock()
    ) == IsReadOnly().has_permission(allowed_request, view=Mock())
    assert ViewPermission().has_permission(
        denied_request, view=Mock()
    ) == IsReadOnly().has_permission(denied_request, view=Mock())

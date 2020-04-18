# -*- coding: utf-8 -*-

from mock import Mock

from django_rest.permissions import (
    BasePermission,
    IsAdmin,
    IsAuthenticated,
    IsReadOnly,
    MetaPermissionOperator,
)


def test_binary_operator_on_permissions_should_return_well_formed_permission():
    ResultPermission = IsAuthenticated | IsAdmin
    assert isinstance(ResultPermission, MetaPermissionOperator)
    assert issubclass(ResultPermission, BasePermission)
    assert ResultPermission.__name__ == "(IsAuthenticated_OR_IsAdmin)"
    assert ResultPermission.__doc__ == "\t({})\n\t{}\n\t({})".format(
        IsAuthenticated.__doc__, "_OR_", IsAdmin.__doc__
    )


def test_unary_operator_on_permission_should_return_well_formed_permission():
    ResultPermission = ~IsAuthenticated
    assert isinstance(ResultPermission, MetaPermissionOperator)
    assert issubclass(ResultPermission, BasePermission)
    assert ResultPermission.__name__ == "(NOT_IsAuthenticated)"
    assert ResultPermission.__doc__ == "\t{}({})".format(
        "NOT_", IsAuthenticated.__doc__
    )


def test_combined_operators_on_permissions_should_return_well_formed_permission():
    ComplexPermission = (IsReadOnly & ~IsAuthenticated) | IsAdmin
    assert isinstance(ComplexPermission, MetaPermissionOperator)
    assert issubclass(ComplexPermission, BasePermission)
    assert (
        ComplexPermission.__name__
        == "((IsReadOnly_AND_(NOT_IsAuthenticated))_OR_IsAdmin)"
    )
    assert (
        ComplexPermission.__doc__
        == "\t(\t({})\n\t{}\n\t(\t{}({})))\n\t{}\n\t({})".format(
            IsReadOnly.__doc__,
            "_AND_",
            "NOT_",
            IsAuthenticated.__doc__,
            "_OR_",
            IsAdmin.__doc__,
        )
    )


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

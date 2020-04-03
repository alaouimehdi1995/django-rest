import pytest
from mock import Mock
from django.http import JsonResponse
from django.contrib.auth.models import User
from django_rest.permissions import (
    AbstractPermission,
    IsAdmin,
    IsAuthenticated,
    IsReadOnly,
    MetaPermissionOperator,
)


def dummy_test_view(request, *args, **kwargs):
    return JsonResponse({}, status=200)


def test_binary_operation_on_permissions_should_return_a_well_formed_permission():
    ComplexPermission = (IsReadOnly & ~IsAuthenticated) | IsAdmin
    assert isinstance(ComplexPermission, MetaPermissionOperator)
    assert issubclass(ComplexPermission, AbstractPermission)
    assert (
        ComplexPermission.__name__
        == "((IsReadOnly_AND_(NOT_IsAuthenticated))_OR_IsAdmin)"
    )
    assert ComplexPermission.__doc__ is not None
    assert len(ComplexPermission.__doc__) > 0


@pytest.mark.django_db
def test_is_admin_permission_should_grant_access_to_admin():
    user = User.objects.create(email="email@test.test", is_superuser=True)
    request = Mock(user=user)
    assert IsAdmin().has_permission(request, dummy_test_view) is True


@pytest.mark.django_db
def test_is_admin_permission_should_forbid_access_to_simple_user():
    user = User.objects.create(email="email@test.test", is_superuser=False)
    request = Mock(user=user)
    assert IsAdmin().has_permission(request, dummy_test_view) is False


@pytest.mark.django_db
def test_is_readonly_permission_should_grant_access_on_GET_request():
    request = Mock(method="GET")
    assert IsReadOnly().has_permission(request, dummy_test_view) is True


@pytest.mark.django_db
def test_is_readonly_permission_should_forbid_acesss_on_POST_request():
    request = Mock(method="POST")
    assert IsReadOnly().has_permission(request, dummy_test_view) is False


@pytest.mark.django_db
def test_is_admin_or_read_only_permission_should_forbid_access_to_non_admin_POST_request():
    IsAdminOrReadOnly = IsAdmin | IsReadOnly
    user = User.objects.create(email="email@test.test", is_superuser=False)
    request = Mock(method="POST", user=user)
    assert IsAdminOrReadOnly().has_permission(request, dummy_test_view) is False


@pytest.mark.django_db
def test_is_admin_or_read_only_permission_should_grant_access_to_non_admin_GET_request():
    IsAdminOrReadOnly = IsAdmin | IsReadOnly
    user = User.objects.create(email="email@test.test", is_superuser=False)
    request = Mock(method="GET", user=user)
    assert IsAdminOrReadOnly().has_permission(request, dummy_test_view) is True


@pytest.mark.django_db
def test_is_admin_or_read_only_permission_should_grant_access_to_admin_POST_request():
    IsAdminOrReadOnly = IsAdmin | IsReadOnly
    user = User.objects.create(email="email@test.test", is_superuser=True)
    request = Mock(method="POST", user=user)
    assert IsAdminOrReadOnly().has_permission(request, dummy_test_view) is True

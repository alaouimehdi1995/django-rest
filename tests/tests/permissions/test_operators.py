# -*- coding: utf-8 -*-

from mock import Mock
import pytest
import six

from django_rest.permissions import (
    BasePermission,
    BinaryOperator,
    IsAdminUser,
    IsAuthenticated,
    IsReadOnly,
    MetaOperand,
    UnaryOperator,
)


def test_binary_operator_on_permissions_should_return_well_formed_permission():
    ResultPermission = IsAuthenticated | IsAdminUser
    assert isinstance(ResultPermission, MetaOperand)
    assert issubclass(ResultPermission, BasePermission)
    assert ResultPermission.__name__ == "(IsAuthenticated_OR_IsAdminUser)"
    assert ResultPermission.__doc__ == "\t({})\n\t{}\n\t({})".format(
        IsAuthenticated.__doc__, "_OR_", IsAdminUser.__doc__
    )


def test_unary_operator_on_permission_should_return_well_formed_permission():
    ResultPermission = ~IsAuthenticated
    assert isinstance(ResultPermission, MetaOperand)
    assert issubclass(ResultPermission, BasePermission)
    assert ResultPermission.__name__ == "(NOT_IsAuthenticated)"
    assert ResultPermission.__doc__ == "\t{}({})".format(
        "NOT_", IsAuthenticated.__doc__
    )


def test_combined_operators_on_permissions_should_return_well_formed_permission():
    ComplexPermission = (IsReadOnly & ~IsAuthenticated) | IsAdminUser
    assert isinstance(ComplexPermission, MetaOperand)
    assert issubclass(ComplexPermission, BasePermission)
    assert (
        ComplexPermission.__name__
        == "((IsReadOnly_AND_(NOT_IsAuthenticated))_OR_IsAdminUser)"
    )
    assert (
        ComplexPermission.__doc__
        == "\t(\t({})\n\t{}\n\t(\t{}({})))\n\t{}\n\t({})".format(
            IsReadOnly.__doc__,
            "_AND_",
            "NOT_",
            IsAuthenticated.__doc__,
            "_OR_",
            IsAdminUser.__doc__,
        )
    )


def test_AND_operator():
    # Given
    class A(BasePermission):
        def has_permission(self, request, view):
            return True

    class B(BasePermission):
        def has_permission(self, request, view):
            return True

    class C(BasePermission):
        def has_permission(self, request, view):
            return False

    # When
    AB = A & B
    AC = A & C

    # Then
    assert AB().has_permission(request=Mock(), view=Mock()) is True
    assert AC().has_permission(request=Mock(), view=Mock()) is False


def test_OR_operator():
    # Given
    class A(BasePermission):
        def has_permission(self, request, view):
            return True

    class B(BasePermission):
        def has_permission(self, request, view):
            return False

    class C(BasePermission):
        def has_permission(self, request, view):
            return False

    # When
    AB = A | B
    BC = B | C

    # Then
    assert AB().has_permission(request=Mock(), view=Mock()) is True
    assert BC().has_permission(request=Mock(), view=Mock()) is False


def test_XOR_operator():
    # Given
    class A(BasePermission):
        def has_permission(self, request, view):
            return True

    class B(BasePermission):
        def has_permission(self, request, view):
            return False

    class C(BasePermission):
        def has_permission(self, request, view):
            return False

    class D(BasePermission):
        def has_permission(self, request, view):
            return True

    # When
    AB = A ^ B
    BC = B ^ C
    AD = A ^ D

    # Then
    assert AB().has_permission(request=Mock(), view=Mock()) is True
    assert BC().has_permission(request=Mock(), view=Mock()) is False
    assert AD().has_permission(request=Mock(), view=Mock()) is False


def test_NOT_operator():
    # Given
    class A(BasePermission):
        def has_permission(self, request, view):
            return True

    class B(BasePermission):
        def has_permission(self, request, view):
            return False

    # When
    NotA = ~A
    NotB = ~B

    # Then
    assert NotA().has_permission(request=Mock(), view=Mock()) is False
    assert NotB().has_permission(request=Mock(), view=Mock()) is True


def test_defining_new_binary_operator_without_overriding_calculate_method_should_raise_error():
    # Given
    class A(BasePermission):
        def has_permission(self, request, view):
            return True

    class B(BasePermission):
        def has_permission(self, request, view):
            return True

    class NewOperator(six.with_metaclass(MetaOperand, BinaryOperator)):
        pass

    # When
    C = NewOperator.build_permission_from(A, B)

    # Then
    with pytest.raises(NotImplementedError):
        C().has_permission(request=Mock(), view=Mock())


def test_defining_new_unary_operator_without_overriding_calculate_method_should_raise_error():
    # Given
    class A(BasePermission):
        def has_permission(self, request, view):
            return True

    class NewOperator(six.with_metaclass(MetaOperand, UnaryOperator)):
        pass

    # When
    C = NewOperator.build_permission_from(A)

    # Then
    with pytest.raises(NotImplementedError):
        C().has_permission(request=Mock(), view=Mock())

# -*- coding: utf-8 -*-

import six

from django_rest.http.methods import SAFE_METHODS


class MetaOperand(type):
    """Metaclass that allows its instances (permission classes) to use logical
    using logical operators (AND, OR, ..) with the follwing syntax:

        FinalPermClass = (Perm1 | Perm2) & ~Perm3

    The `OPERATOR_NAME` class attribute is used to build a name for the resulting
    class of an unary/binary operation. For example:

        FinalPermClass = (Perm1 | Perm2) & ~Perm3
        FinalPermClass.__class__.__name__
        # ((Perm1_OR_Perm2)_And_(Not_Perm3))

    """

    OPERATOR_NAME = None

    def __and__(first_class, second_class):
        # type:(ClassVar, ClassVar) -> ClassVar
        return AND.build_permission_from(first_class, second_class)

    def __or__(first_class, second_class):
        # type:(ClassVar, ClassVar) -> ClassVar
        return OR.build_permission_from(first_class, second_class)

    def __xor__(first_class, second_class):
        # type:(ClassVar, ClassVar) -> ClassVar
        return XOR.build_permission_from(first_class, second_class)

    def __invert__(first_class):
        # type:(ClassVar, ClassVar) -> ClassVar
        return NOT.build_permission_from(first_class)


# == Abstract operators


class BinaryOperator(object):
    """Class that describes how to build a permission class as a result of a
    Binary operators only. The current class is intended to be inherited by operators
    like: `AND`, `OR`, `XOR`, etc.

    The method called during operations is `build_permission_class()`. It creates
    a new permission class (i.e. inheriting from `BasePermission`), for which
    the `has_permission()` method is built using the `calculate()` method on both
    `has_permission()` results of operand classes.

    A new binary operator can be created by inheriting both the current class, and
    defining `MetaOperand` as metaclass, then implementing the `calculate()`
    staticmethod.
    Example:

        class MyNewBinaryOperator(BinaryOperator, metaclass=MetaOperand):
            @staticmethod
            def calculae(value1, value2):
                # type:(bool, bool) -> bool
                return fn(value1, value2)

    Then, in order to make the new operator used (without having to always call
    `MyNewBinaryOperator.build_permission_from(class1, class2)`, it should be
    subscribed in the `MetaOperand`. For example, in order to use the new operator
    with the `+`, it should be assigned in the `__add__` method of `MetaOperand`
    """

    @staticmethod
    def calculate(first_function, second_function, *args, **kwargs):
        # type:(Callable, Callable, *Any, **Any) -> bool
        raise NotImplementedError(
            "`calculate()` method should be defined in subclasses"
        )

    @classmethod
    def build_classname(cls, class_1, class_2):
        # type:(ClassVar, ClassVar) -> str
        return "({}{}{})".format(class_1.__name__, cls.OPERATOR_NAME, class_2.__name__)

    @classmethod
    def build_docstring(cls, class_1, class_2):
        # type:(ClassVar, ClassVar) -> str
        return "\t({})\n\t{}\n\t({})".format(
            class_1.__doc__, cls.OPERATOR_NAME, class_2.__doc__
        )

    @classmethod
    def build_permission_from(cls, permission_class_1, permission_class_2):
        # type:(ClassVar, ClassVar) -> ClassVar
        result_classname = cls.build_classname(permission_class_1, permission_class_2)
        result_class = MetaOperand(result_classname, (BasePermission,), {})
        result_class.__doc__ = cls.build_docstring(
            permission_class_1, permission_class_2
        )

        def has_permission(self, request, view):
            # type:(HttpRequest, Callable) -> bool
            permission_func_1 = permission_class_1().has_permission
            permission_func_2 = permission_class_2().has_permission
            return cls.calculate(permission_func_1, permission_func_2, request, view)

        result_class.has_permission = has_permission
        return result_class


class UnaryOperator(object):
    """Class that describes how to build a permission class as a result of a
    Unary operators only. The current class is intended to be inherited by operators
    like: `NOT` and Identity operators.

    The method called during operations is `build_permission_class()`. It creates
    a new permission class (i.e. inheriting from `BasePermission`), for which
    the `has_permission()` method is built using the `calculate()` method on the
    `has_permission()` result of operand class.

    A new unary operator can be created by inheriting both the current class, and
    defining `MetaOperand` as metaclass, then implementing the `calculate()`
    staticmethod.
    Example:

        class MyNewUnaryOperator(UnaryOperator, metaclass=MetaOperand):
            @staticmethod
            def calculae(value):
                # type:(bool) -> bool
                return fn(value)
    """

    OPERATOR_NAME = None

    @staticmethod
    def calculate(function, *args, **kwargs):
        # type:(Callable, *Any, **Any) -> bool
        raise NotImplementedError(
            "`calculate()` method should be defined in subclasses"
        )

    @classmethod
    def build_classname(cls, _class):
        # type:(ClassVar) -> str
        return "({}{})".format(cls.OPERATOR_NAME, _class.__name__)

    @classmethod
    def build_docstring(cls, _class):
        # type:(ClassVar, ClassVar) -> str
        return "\t{}({})".format(cls.OPERATOR_NAME, _class.__doc__)

    @classmethod
    def build_permission_from(cls, permission_class):
        # type:(ClassVar) -> ClassVar
        result_classname = cls.build_classname(permission_class)
        result_class = MetaOperand(result_classname, (BasePermission,), {})
        result_class.__doc__ = cls.build_docstring(permission_class)

        def has_permission(self, request, view):
            # type:(HttpRequest, Callable) -> bool
            permission_func = permission_class().has_permission
            return cls.calculate(permission_func, request, view)

        result_class.has_permission = has_permission
        return result_class


# == Concrete operators


class AND(six.with_metaclass(MetaOperand, BinaryOperator)):
    """AND Logical operator class.

    Example of use:

        ResultPermClass = AND.build_permission_from(PermClass1, PermClass2)
        # Which is also equivalend to:
        ResultPermClass = PermClass1 & PermClass2
    """

    OPERATOR_NAME = "_AND_"

    @staticmethod
    def calculate(first_function, second_function, *args, **kwargs):
        # type:(Callable, Callable, *Any, **Any) -> bool
        return first_function(*args, **kwargs) and second_function(*args, **kwargs)


class OR(six.with_metaclass(MetaOperand, BinaryOperator)):
    """OR Logical operator class.

    Example of use:

        ResultPermClass = OR.build_permission_from(PermClass1, PermClass2)
        # Which is also equivalend to:
        ResultPermClass = PermClass1 | PermClass2
    """

    OPERATOR_NAME = "_OR_"

    @staticmethod
    def calculate(first_function, second_function, *args, **kwargs):
        # type:(Callable, Callable, *Any, **Any) -> bool
        return first_function(*args, **kwargs) or second_function(*args, **kwargs)


class XOR(six.with_metaclass(MetaOperand, BinaryOperator)):
    """XOR (eXclusive OR) Logical operator class.

    Example of use:

        ResultPermClass = XOR.build_permission_from(PermClass1, PermClass2)
        # Which is also equivalend to:
        ResultPermClass = PermClass1 ^ PermClass2
    """

    OPERATOR_NAME = "_XOR_"

    @staticmethod
    def calculate(first_function, second_function, *args, **kwargs):
        # type:(Callable, Callable, *Any, **Any) -> bool
        return first_function(*args, **kwargs) ^ second_function(*args, **kwargs)


class NOT(six.with_metaclass(MetaOperand, UnaryOperator)):
    """NOT Logical operator class.

    Example of use:

        ResultPermClass = NOT.build_permission_from(PermClass)
        # Which is also equivalend to:
        ResultPermClass = ~PermClass
    """

    OPERATOR_NAME = "NOT_"

    @staticmethod
    def calculate(function, *args, **kwargs):
        # type:(Callable, *Any, **Any) -> bool
        return not function(*args, **kwargs)


class BasePermission(six.with_metaclass(MetaOperand, object)):
    """
    The Mainclass of all existing permissions. It's created with `MetaOperand`,
    which allows it to use operators such as: `&`, `|` `^` and `~`.

    A new custom permission could be created by inheriting from the current class,
    and implementing the `has_permission()` method, as shown in the following example:

        class FooBarPermission(BasePermission):
            def has_permission(self, request, view):
                return request.user.name in ("foo", "bar")
    """

    def has_permission(self, request, view):
        # type:(HttpRequest, Callable) -> bool
        raise NotImplementedError(
            "`has_permission()` method should be defined in subclasses"
        )


class AllowAny(BasePermission):
    """
    Allows everybody to access the view.
    """

    def has_permission(self, request, view):
        # type:(HttpRequest, Callable) -> bool
        return True


class IsAuthenticated(BasePermission):
    """
    Allows the view access to authenticated users only.
    """

    def has_permission(self, request, view):
        # type:(HttpRequest, Callable) -> bool
        return bool(request.user and request.user.is_authenticated)


class IsStaffUser(BasePermission):
    """
    Allows the view access to staff users only.
    """

    def has_permission(self, request, view):
        # type:(HttpRequest, Callable) -> bool
        return bool(request.user and request.user.is_staff)


class IsAdminUser(BasePermission):
    """
    Allows the view access to admin users only.
    """

    def has_permission(self, request, view):
        # type:(HttpRequest, Callable) -> bool
        return bool(request.user and request.user.is_superuser)


class IsReadOnly(BasePermission):
    """
    Allows the view access to read-only http methods: GET, HEAD and OPTIONS.
    """

    def has_permission(self, request, view):
        # type:(HttpRequest, Callable) -> bool
        return request.method in SAFE_METHODS


IsAuthenticatedOrReadOnly = IsAuthenticated | IsReadOnly

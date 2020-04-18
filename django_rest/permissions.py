# -*- coding: utf-8 -*-


class MetaPermissionOperator(type):
    """
    Base Metaclass that allows us to build permission classes dynamically
    using logical operators (AND, OR, ..) with the follwing syntaxes (equivalent):
    FinalPermClass = (Perm1 | Perm2) & ~Perm3
    FinalPermClass = (Perm1 or Perm2) and not Perm3
    The `OPERATOR_NAME` attribute is used to build a name for the resulting class of
    an unary/binary operation. For example, the resulting class of the example above
    will be named: `((Perm1_OR_Perm2)_And_(Not_Perm3))`
    """

    OPERATOR_NAME = None

    def __and__(first_class, second_class):
        # type:(class, class) -> class
        return AND.build_permission_from(first_class, second_class)

    def __or__(first_class, second_class):
        # type:(class, class) -> class
        return OR.build_permission_from(first_class, second_class)

    def __xor__(first_class, second_class):
        # type:(class, class) -> class
        return XOR.build_permission_from(first_class, second_class)

    def __invert__(first_class):
        # type:(class, class) -> class
        return NOT.build_permission_from(first_class)


class MetaPermissionBinaryOperator(MetaPermissionOperator):
    """
    Metaclass that implements how the resulting permission class is built as a result
    of a Binary operators only. This Metaclass is intended to be inherited by operators
    like: `AND`, `OR`, `XOR`, etc.
    """

    @staticmethod
    def calculate(value1, value2):
        # type:(bool, bool) -> bool
        raise NotImplementedError(
            "`calculate()` method should be defined in subclasses"
        )

    @classmethod
    def build_classname(cls, class_1, class_2):
        # type:(class, class) -> str
        return "({}{}{})".format(class_1.__name__, cls.OPERATOR_NAME, class_2.__name__)

    @classmethod
    def build_docstring(cls, class_1, class_2):
        # type:(class, class) -> str
        return "\t({})\n\t{}\n\t({})".format(
            class_1.__doc__, cls.OPERATOR_NAME, class_2.__doc__
        )

    @classmethod
    def build_permission_from(cls, first_perm_class, second_perm_class):
        # type:(class, class) -> class
        result_classname = cls.build_classname(first_perm_class, second_perm_class)
        result_class = MetaPermissionOperator(result_classname, (BasePermission,), {})
        result_class.__doc__ = cls.build_docstring(first_perm_class, second_perm_class)

        def has_permission(self, *args, **kwargs):
            first_result = first_perm_class().has_permission(*args, **kwargs)
            second_result = second_perm_class().has_permission(*args, **kwargs)
            return cls.calculate(first_result, second_result)

        result_class.has_permission = has_permission
        return result_class


class MetaPermissionUnaryOperator(MetaPermissionOperator):
    """
    Metaclass that implements how the resulting permission class is built as a result
    of a Unary operators only. This Metaclass is intended to be inherited by operators
    like `NOT` and `ID` (identity).
    """

    OPERATOR_NAME = None

    @staticmethod
    def calculate(value):
        # type:(bool) -> bool
        raise NotImplementedError(
            "`calculate()` method should be defined in subclasses"
        )

    @classmethod
    def build_classname(cls, _class):
        # type:(class) -> str
        return "({}{})".format(cls.OPERATOR_NAME, _class.__name__)

    @classmethod
    def build_docstring(cls, _class):
        # type:(class, class) -> str
        return "\t{}({})".format(cls.OPERATOR_NAME, _class.__doc__)

    @classmethod
    def build_permission_from(cls, permission_class):
        # type:(class) -> class
        result_classname = cls.build_classname(permission_class)
        result_class = MetaPermissionOperator(result_classname, (BasePermission,), {})
        result_class.__doc__ = cls.build_docstring(permission_class)

        def has_permission(*args, **kwargs):
            result = permission_class().has_permission(*args, **kwargs)
            return cls.calculate(result)

        result_class.has_permission = has_permission
        return result_class


class AND(MetaPermissionBinaryOperator):
    OPERATOR_NAME = "_AND_"

    @staticmethod
    def calculate(value1, value2):
        # type:(bool, bool) -> bool
        return value1 and value2


class OR(MetaPermissionBinaryOperator):
    OPERATOR_NAME = "_OR_"

    @staticmethod
    def calculate(value1, value2):
        # type:(bool, bool) -> bool
        return value1 or value2


class XOR(MetaPermissionBinaryOperator):
    OPERATOR_NAME = "_XOR_"

    @staticmethod
    def calculate(value1, value2):
        # type:(bool, bool) -> bool
        return value1 ^ value2


class NOT(MetaPermissionUnaryOperator):
    OPERATOR_NAME = "NOT_"

    @staticmethod
    def calculate(value):
        # type:(bool) -> bool
        return not value


class IdentityOperator(MetaPermissionUnaryOperator):
    OPERATOR_NAME = ""  # The resulting class preserves the same name.

    @staticmethod
    def calculate(value):
        # type:(bool) -> bool
        return value


class BasePermission(object):
    __metaclass__ = IdentityOperator

    def has_permission(self, request, view):
        raise NotImplementedError(
            "`has_permission()` method should be defined in subclasses"
        )


class AllowAny(BasePermission):
    """
    Allows everybody to access the view.
    """

    def has_permission(self, request, view):
        return True


class IsAuthenticated(BasePermission):
    """
    Allows the view access to authenticated users only.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsStaff(BasePermission):
    """
    Allows the view access to staff users only.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAdmin(BasePermission):
    """
    Allows the view access to admin users only.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsReadOnly(BasePermission):
    """
    Allows the view access to read-only http methods: GET, HEAD and OPTIONS.
    """

    SAFE_HTTP_METHODS = ("GET", "HEAD", "OPTIONS")

    def has_permission(self, request, view):
        return request.method in self.SAFE_HTTP_METHODS


IsAuthenticatedOrReadOnly = IsAuthenticated | IsReadOnly

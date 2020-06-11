# django-flash-REST

# Overview

django-flash-REST is a **tiny**, **lightweight**, **easy-to-use** and **incredibly fast** library to implement
REST views with django. The whole library's focused in **one** decorator that transforms the
simple views into REST ones, allowing easy customizations (such as permissions, serializers, etc.)

The library itself was highly inspired from the great [django-rest-framework](https://www.django-rest-framework.org/) and [SerPy](https://serpy.readthedocs.io/en/latest/)

# Table of contents

1. [Overview](#overview)
2. [Table of contents](#table-of-contents)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Example](#example)
6. [Documentation](#documentation)

   1. [The @api_view decorator](#1-the-api_view-decorator)
      1. [Decorator argments](#11-decorator-arguments)
      2. [Decorated view's arguments](#12-decorated-views-arguments)
      3. [How to decorate a view](#13-how-to-decorate-a-view)
   2. [View Permissions](#2-view-permissions)
      1. [Introduction](#21-introduction)
      2. [Available Permissions](#22-available-permissions)
      3. [Permissions Operators](#23-permissions-operators)
      4. [Implement your own permission](#24-implement-your-own-permission)
   3. [Deserializers](#3-deserializers)
      1. [Introduction](#31-introduction)
      2. [Impmement a new Deserializer](#32-implement-a-new-deserializer)
      3. [Available Deserializer Fields](#33-available-deserializer-fields)
      4. [Nested Deserializers](#34-nested-deserializers)
      5. [Post-clean methods](#35-post-clean-methods)
      6. [All-pass Deserializer](#36-all-pass-deserializer)
   4. [Serializers](#4-serializers)
      1. [Introduction](#41-introduction)
      2. [Impmement a new Serializer](#42-implement-a-new-serializer)
      3. [Available Serializer Fields](#43-available-serializer-fields)
         1. [Primitive types](#1-primitive-types)
         2. [MethodField](#2-methodfield)
         3. [ConstantField](#3-constantfield)
         4. [ListField](#4-listfield)
      4. [Nested Serializers](#44-nested-serializers)
      5. [DictSerializer](#45-dictserializer)
   5. [Exceptions](#5-exceptions)
      1. [@api_view exceptions catching](#51-api_view-exceptions-catching)
      2. [Existing API Exceptions](#52-existing-api-exceptions)
      3. [Define your own API Exception](#53-define-your-own-api-exception)
   6. [HTTP](#6-http)
      1. [HTTP Status codes](#62-http-status-codes)
      2. [HTTP Methods](#63-http-methods)

# Requirements

django-flash-REST library requires:

-  Python version 2.7+ or 3.3+
-  django version 1.10+

# Installation

You can get the package using `pip`, as the following:

```bash
pip install django-flash-rest
```

# Example

Let's implement a quick public API endpoint that lists existing regular (_i.e._ not staff) users:

First, start a new django project:

```sh
pip install django-flash-rest # Will install django if not already installed
django-admin startproject first_project .
./manage.py migrate
./manage.py createsuperuser
# Follow instructions
```

Let's get started by implementing the views in `./first_project/urls.py`:

```python
from typing import Dict

from django.contrib import admin
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import path

from flash_rest.decorators import api_view
from flash_rest.http import status
from flash_rest.serializers import fields as fields, Serializer


# The serializer defines the output format of our endpoints
class UserSerializer(Serializer):
    id = fields.IntegerField()
    username = fields.CharField()
    email = fields.CharField()
    is_staff = fields.BooleanField()


@api_view(allowed_methods=["GET"])
def list_users_view(request, url_params: Dict, query_params: Dict, **kwargs):
    regular_users = User.objects.exclude(is_staff=True)
    return JsonResponse(
        UserSerializer(regular_users, many=True).data,
        status=status.HTTP_200_OK,
        safe=False,
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", list_users_view),
]
```

That's all! Now run the server:

```sh
./manage.py runserver
```

In order to test your endpoints, you can use [PostMan](https://www.postman.com/), [httpie](https://httpie.org/) or [curl](https://curl.haxx.se/).
I'll be using `httpie` in the example:

```sh
http GET http://127.0.0.1:8000/api/users/

HTTP/1.1 200 OK
Content-Length: 84
Content-Type: application/json
Date: Sat, 30 May 2020 02:13:49 GMT
Server: WSGIServer/0.2 CPython/3.6.9
X-Content-Type-Options: nosniff
X-Frame-Options: DENY

[]

# After creating a new user from django-admin section (visit: http://127.0.0.1:8000/admin/ using your browser)

http GET http://127.0.0.1:8000/api/users/

HTTP/1.1 200 OK
Content-Length: 84
Content-Type: application/json
Date: Sat, 30 May 2020 02:17:23 GMT
Server: WSGIServer/0.2 CPython/3.6.9
X-Content-Type-Options: nosniff
X-Frame-Options: DENY

[
    {
        "email": "myfirst@user.com",
        "id": 1,
        "is_staff": true,
        "username": "firstuser"
    }
]

```

# Documentation

## 1. The `@api_view` decorator

### 1.1 Decorator arguments

As shown in the example section, the `@api_view` could be used with multiple
(optional) arguments:

```python
api_view(
    permission_class: BasePermission = AllowAny,
    allowed_methods: Iterable[str] = ALL_HTTP_METHODS,
    deserializer_class: Union[
        Deserializer, Dict[str, Deserializer]
    ] = AllPassDeserializer,
    allow_forms: bool = False,
)
```

1. **permission_class**

   A class that defines who is allowed to access the
   decorated view. If no `permission_class` given, the decorator's default permission is
   `AllowAny` (your view is public).

   In case the user isn't allowed to access the view,
   a `403 Forbidden access` response will be returned before even executing the
   view's code. More details in [permissions section](#2-view-permissions).

2. **allowed_methods**:

   A `list`/`tuple` of HTTP allowed methods. Allowed methods should
   be in uppercase strings (_ex.`GET`, `POST`, etc._). You can also use some
   predefined sets in `flash_rest.http.methods`. If no `allowed_methods`
   given, all HTTP methods will be allowed.

   If the user requests the decorated view
   with a non-allowed method, a `405 Method not allowed` response will be
   returned before executing your view's code.

3. **deserializer_class**:

   Could be either a sub-class of `Deserializer` (as shown in the
   previous example), or a `dict` that maps HTTP methods that use payload (_i.e._ `POST`, `PUT`
   and `PATCH`) to `Deserializer` sub-classes, as the following:

   ```python
   @api_view(deserializer_class=MyDeserializerClass)
   def first_case_view(request, **kwargs):
      # [...]

   @api_view(
      deserializer_class={
         "POST": MyCustomPOSTDeserializer,
         "PUT": MyCustomPUTDeserializer,
      },
   )
   def second_case_view(request, **kwargs):
      # [...]
   ```

   In the first case above, `MyDeserializerClass` will be applied to: `POST`,
   `PUT` and `PATCH` methods. Also, note that in second case, the `deserializer_class` mapping doesn't
   define a deserializer for the `PATCH` HTTP method. In this case,
   the "all-pass" deserializer (_i.e._ passes payload data to the view without any
   validation) will be used. The same deserializer will be applied if no
   `deserializer_class` is given.

   If the payload data doesn't respect the format defined in the deserializer,
   a `400 Bad Request` response will be returned.

4. **allow_forms**:

   A `bool` that allows/forbids payloads coming from forms (
   `application/x-www-form-urlencoded` and `multipart/form-data` content-types).

   A `415 Unsupported Media Type` response will be returned in case the user sends form
   data to a view decorated with `allow_forms=False`. The argument's default value is `False`.

### 1.2 Decorated view's arguments

As illustrated in the examples above, the `@api_view` decorator alters the
decorated view's arguments. The decorator gathers, extracts and standardizes
different arguments, then passes them to your view, in order to facilitate their
use. Let's explain each argument:

```python
@api_view
def decorated_view(
    request: HttpRequest,
    url_params: Dict[str, Any],
    query_params: Dict[str, str],
    deserialized_data: Optional[Dict[str, Any]],
) -> JsonResponse:
   # For class methods, the first argument is `self` (the class instance)
   # [...]
```

1. **request**:

   django's native request object (`django.http.request.HttpRequest`). Similar
   to every django view's first argument.
   More details on [django's documentation](https://docs.djangoproject.com/en/3.0/ref/request-response/)

2. **url_params**:

   A `dict` containing the parameter defined in your view's
   route (django router). For example, let's take a look to `url_params` when requesting the URL `/api/hello/foo/bar/25/` in the following example:

   ```python
   # urls.py
   from django.urls import path
   from flash_rest.decorators import api_view

   @api_view
   def hello_view(request, url_params, query_params, **kwargs):
      #  url_params = {"first_name": "foo", "last_name": "bar", "age": 25}

   urlpatterns = [
      path("api/hello/<str:first_name>/<str:last_name>/<int:age>/", hello_view),
   ]
   ```

   **Important note:** The parameters are already casted into their target types (_in
   the example above, `url_params['age']` is `int`, while `url_params['first_name']` is `str`_)

3. **query_params**:

   A `dict` containing all the query parameters encoded in the request's URL.
   Let's request the previous example's view with the following URL:`/api/hello/foo/bar/25/?lang=fr&display=true`:

   ```python
   # views.py
   @api_view
   def hello_view(request, url_params, query_params, **kwargs):
      #  url_params = {"first_name": "foo", "last_name": "bar", "age": 25}
      #  query_params = {"lang": "fr", "display": "true"}

   ```

   **Important note:** Unlike `url_params`, for query parameters, the values are **ALWAYS** strings (`str`), and
   they should be casted manually.

4. **deserialized_data**:

   A `dict` with the data validated by the deserializer. For HTTP
   methods without payload (`GET`, `DELETE`, _etc._), this argument's value is
   `None`.

   As explained in the section before, for HTTP methods requiring
   data, if no `deserializer_class`'s been given to the decorator, `deserialized_data`
   will contain the raw payload's data (without any validation).

**Note:** In case you want to ignore a argument (let's say `deserialized_data`
for a `GET` view), add `**kwargs` argument to your view. Otherwise, you'll have
a arguments error.

### 1.3 How to decorate a view

The `@api_view` decorator could be applied differently on the views, depending on your use-case. You can:

1. Decorate a function-based view. For example:
   ```python
   @api_view(allowed_methods=['GET'])
   def hello_view(request, **kwargs):
      return JsonResponse({'message': 'Hello world'}, status=200)
   ```
2. Decorate a whole class-based view (should be a sub-class of `django.view.View`). For example:

   ```python
   @api_view(permission_class=IsStaffUser)
   class HelloView(View):
      def get(self, request, **kwargs):
         return JsonResponse({"message": "Hello world"}, status=200)

      def post(self, request, **kwargs):
         return JsonResponse({}, status=201)

      def other_method(self, arg_1, arg_2):
         # [...]
   ```

   For class-based views, the decorator decorates all view's http methods
   (`get()`, `post()`, `put()`, _etc._) and **ONLY** them. In the example above, all http methods are restricted for staff-users only, but `other_method` method hasn't been altered.

**Note:** Both `@api_view()` and `@api_view` syntaxes are correct in case the decorator is used without arguments.

## 2. View Permissions

### 2.1 Introduction

Permissions is what determines whether a request should be granted or denied
access, for a particular view. The inspection process is done before executing
the decorated view's code, then, if the request satisfies the
permission's constraints, the access is granted. If not, a `403 Forbidden access`
response is returned.

In django-flash-REST, all permissions inherit from `Permission`, and passed as argument to the `@api_view` decorator, as seen in
the previous examples.

In this section, we will start by introducing the django-flash-REST's provided
permissions, then how to build more complex permissions by combining the
existing ones, and finally, how to implement your own custom permission.

### 2.2 Available Permissions

All the permissions listed below could be imported from `flash_rest.permissions`

-  **AllowAny**:
   By choosing this permission, your view will be public (all requests will have granted access). It's the default permission for `@api_view` decorator.
-  **IsAuthenticated**:
   Allows only authenticated users to access your view. Anonymous users (_i.e._ not authenticated) receive a `403 Forbidden access` response.
-  **IsStaffUser**:
   The view can be accessed by staff users only. A staff user is a `User` object having `is_staff` attribute set to `True`.
-  **IsAdminUser**:
   Admins are the only users who can access the decorated view. An admin is a `User` object having `is_superuser` attribute set to `True`.
-  **IsReadOnly**:
   Only HTTP safe methods (`GET`, `HEAD` and `OPTIONS`) are allowed. For a `POST` request for example, the user receives a `403 Forbidden access`.

   This permission is not meant to be used in standalone, because, remember, the `@api_view` decorator has already the `allowed_methods` argument for this purpose, that returns a `405 Method not allowed`.
   It has been implemented only to be combined with other permissions in order to build a more complex ones (the next permission on the list is a good example).

-  **IsAuthenticatedOrReadOnly**:
   This permission allows Authenticated users to use all HTTP methods (`GET`, `POST`, `DELETE`, _etc._), and anonymous users to use safe methods only (`GET`, `HEAD` and `OPTIONS`).

### 2.3 Permissions Operators

Using logical operators allows you to combine different `Permission` sub-classes, in a simple and powerful way, to obtain more complex and complete permissions.

django-flash-REST provides you 4 logical operators: **AND** (`&`), **OR** (`|`), **XOR** (`^`) and **NOT** (`~`).

Let's demonstrate those operators then their combinations in concrete examples:

1. **AND operator**:

Let's create a new `IsStaffAndReadOnly` permission that grants access to:

-  Staff users, **and** only with reading http methods (`GET`, `HEAD` and `OPTIONS`).

It will be implemented as the following:

```python
from flash_rest.decorators import api_view
from flash_rest.permissions import IsReadOnly, IsStaffUser

IsStaffAndReadOnly = IsStaffUser & IsReadOnly

@api_view(permission_class=IsStaffAndReadOnly)
def target_view(request, **kwargs):
    # [...]
```

2. **OR operator**:

Let's create a new `IsAdminOrReadOnly` permission granting access to:

-  Admin users with all HTTP methods
-  Non-admin users with reading http methods (`GET`, `HEAD` and `OPTIONS`) only.

```python
from flash_rest.decorators import api_view
from flash_rest.permissions import IsAdminUser, IsReadOnly

IsAdminOrReadOnly = IsAdminUser | IsReadOnly

@api_view(permission_class=IsAdminOrReadOnly)
def target_view(request, **kwargs):
    # [...]
```

3. **XOR (_eXclusive OR_) operator**:

For this example, let's implement a permission that grants access to:

-  Users that are staff
-  Users that are **not** admins

Note that this permission could be implemented differently (and in a more
correct and readable way). The use of XOR operator here is for demonstration purpose only.
The correct implementation is shown below in "_5. Combining Operators_" example.

```python
from flash_rest.decorators import api_view
from flash_rest.permissions import IsAdminUser, IsStaffUser

IsStaffAndNotAdminUser = IsAdminUser ^ IsStaffUser

@api_view(permission_class=IsStaffAndNotAdminUser)
def target_view(request, **kwargs):
    # [...]
```

4. **NOT operator**:

Let's consider a view that should be exposed to anonymous (_i.e._ not
authenticated) users only. This view's permission will be defined as the following:

```python
from flash_rest.decorators import api_view
from flash_rest.permissions import IsAuthenticated

AnonymousUserOnly = ~IsAuthenticated

@api_view(permission_class=AnonymousUserOnly)
def target_view(request, **kwargs):
    # [...]
```

5. **Combining Operators**:

Let's re-implement the `IsStaffAndNotAdminUser` used in the XOR example above, by using
multiple operators. Then, we'll re-use it (`IsStaffAndNotAdminUser`) to implement a new
`IsStaffAndNotAdminUserOrReadOnly`:

```python
from flash_rest.decorators import api_view
from flash_rest.permissions import IsAdminUser, IsReadOnly, IsStaffUser

IsStaffAndNotAdminUser = IsStaffUser & (~ IsAdminUser)

IsStaffAndNotAdminUserOrReadOnly = IsStaffAndNotAdminUser | IsReadOnly
# Or: IsStaffAndNotAdminUserOrReadOnly = (IsStaffUser & (~ IsAdminUser)) | IsReadOnly

@api_view(permission_class=IsStaffAndNotAdminUserOrReadOnly)
def target_view(request, **kwargs):
    # [...]
```

### 2.4 Implement your own permission

Even if combining standard permissions covers the most usual use-cases, you may have some unusual constrains that cannot be tackled using existing operators only.

django-flash-REST provides you a way to implement a custom permission that fits your needs.
All you have to do is inherit from `flash_rest.permissions.BasePermission`, then implement the `has_permission()` method.

The `has_permission()` takes the `request` object, and the target view object as
arguments, and should return a `bool` that represents if the access should be
granted (`True`) or not (`False`).

```python
def has_permission(self, request: HttpRequest, view:Union[Callable, View]) -> bool:
```

Let's implement a custom permission that grants access to authenticated users
having `gmail` address only. The "authenticated users" part will be taken care
of using the existing `IsAuthenticated` permission.

```python
from flash_rest.decorators import api_view
from flash_rest.permissions import BasePermission, IsAuthenticated


class HasGmailAddress(BasePermission):
    def has_permission(self, request, view):
        user_email = request.user.email
        domain_name = user_email.split('@')[1]
        has_gmail_address = (domain_name == 'gmail.com')
        return has_gmail_address


@api_view(permission_class=IsAuthenticated & HasGmailAddress)
def target_view(request, **kwargs):
    # [...]
```

**Important Note:**

While using operators, operands order **matters**.

In the example above, in `HasGmailAddress` code, we assumed that the user is
already authenticated, instead of manually checking it. That's because if the permission `IsAuthenticated` isn't satisfied,
django-flash-REST returns a `403 Forbidden access` before even evaluating `HasGmailAddress` permission.
That's why in `HasGmailAddress` code, we assumed the user is authenticated.

If we switched permissions order as the following:

```python
@api_view(permission_class=HasGmailAddress & IsAuthenticated)
def target_view(request, **kwargs):
    # [...]
```

We should have added a condition in `HasGmailAddress` to verify if the user is
authenticated (and therefore, `IsAuthenticated` permission will be useless).
Otherwise, if an anonymous user requests the view, a `AttributeError: 'NoneType' object has no attribute 'email'` exception will be raised.

## 3. Deserializers

### 3.1. Introduction

In django-flash-REST, a deserializer validates input data (request payload and/or form data)
based on custom fields ans constrains defined in the deserializer class,
then "translates" data into the target format (Python primitive types), and finally
executes some post-validation methods (if defined).
In this chapter, we'll cover how to implement a simple deserializer, what are the
fields available for use, how to nest deserializers for more complex validation and to post-clean your data,
and finally, what the `AllPassDeserializer` is.

### 3.2. Implement a new Deserializer

Defining a new `Deserializer` is quite simple. All you need to do is to inherit
from `Deserializer` class:

```python
from flash_rest.deserializers import Deserializer


class MyCustomDeserializer(Deserializer):
    pass
```

But, a deserializer class has no purpose without its fields. Let's define
a simple `Deserializer` with 2 fields: a positive integer primary key (`pk`),
and a `username` (string).

```python
from flash_rest.deserializers import fields, Deserializer


class MyCustomDeserializer(Deserializer):
    pk = fields.IntegerField(min_value=0)  # Implicit required
    username = fields.CharField(required=True)  # Explicit required
```

That's how a `Deserializer` is defined. Now, if you want to use the deserializer
outside the `@api_view`'s `deserializer_class` argument, you have two approaches to proceed:

#### The first approach

1. Instantiate your deserializer class, passing `data` argument to the
   constructor.
2. Check your data validity, by calling `.is_valid()` method.
3. Retrieve the validated data with `.data` (or errors with `.errors`)
   attribute.

Here is a simple example:

```python
from flash_rest.deserializers import fields, Deserializer


class MyCustomDeserializer(Deserializer):
    pk = fields.IntegerField(min_value=0)
    username = fields.CharField(required=True)


valid_input = {'pk': '3', 'username': 'foobar'}
invalid_input = {'pk': -3, 'username': 'foobar'}

valid_instance = MyCustomDeserializer(data=valid_input)
valid_instance.is_valid()  # True
valid_instance.data  # {'pk': 3, 'username': 'foobar'}

invalid_instance = MyCustomDeserializer(data=invalid_input)
invalid_instance.is_valid()  # False
invalid_instance.errors  # {"pk": ["Ensure this value is greater than or equal to 0."]}
```

#### The second approach

1. Instantiate the deserializer class without arguments.
2. Call the `.clean()` method with the data to validate, it should return the
   valid data, or raise a `ValidationError` in case the input data is invalid.
3. Put the clean call inside a `try/except` clause to catch the validation errors.

Here is a simple example:

```python
from flash_rest.deserializers import fields, Deserializer, ValidationError


class MyCustomDeserializer(Deserializer):
    pk = fields.IntegerField(min_value=0)
    username = fields.CharField(required=True)


valid_input = {'pk': '3', 'username': 'foobar'}
invalid_input = {'pk': -3, 'username': 'foobar'}

deserializer_instance = MyCustomDeserializer()

deserializer.clean(valid_input)  # {'pk': 3, 'username': 'foobar'}

try:
    data = deserializer.clean(invalid_input)
except ValidationError as errors:
    errors = dict(errors)  # errors = {"pk": ["Ensure this value is greater than or equal to 0."]}
    do_something_with_errors(errors)
else:
    do_something(data)
```

### 3.3. Available Deserializer Fields

django-flash-REST deserializers use native django forms fields. **Depending on the
django version you are using**, you may have access (or not) to some fields, and some of
their attributes. More details on [django's official doc](https://docs.djangoproject.com/en/3.0/ref/forms/fields/).

**Important Note:** You can enjoy **every** feature available in django forms fields, such as
[custom validators](https://docs.djangoproject.com/en/3.0/ref/validators/) and
[custom error messages](https://docs.djangoproject.com/en/3.0/ref/forms/fields/#error-messages)

### 3.4 Nested Deserializers

django-flash-REST offers support for nesting deserializers, in order to build more complex ones, in a flexible way and without losing readability.

By nesting deserializers, errors are nested, and output data is a nested `dict`
too. The following example illustrates how to nest deserializers:

```python
from django.core.validators import MinValueValidator, MaxValueValidator
from flash_rest.deserializers import fields, Deserializer


class RaceDriverDeserializer(Deserializer):
    first_name = fields.CharField(required=True)
    last_name = fields.CharField(required=True)
    birth_day = fields.DateField()


class RaceCarDeserializer(Deserializer):
    brand = fields.CharField()
    model = fields.CharField()
    production_year = fields.IntegerField(
        required=False, validators=[MinValueValidator(1900), MaxValueValidator(2020)]
    )
    driver = RaceDriverDeserializer(required=True)


valid_data = {
    "brand": "Mercedes",
    "model": "C11",
    "production_year": "1990",
    "driver": {
        "first_name": "Michael",
        "last_name": "Schumacher",
        "birth_day": "1969-01-03",
    },
}

deserializer = RaceCarDeserializer(data=valid_data)
deserializer.is_valid()  # True
deserializer.data
"""
{
   'brand': 'Mercedes',
   'model': 'C11',
   'production_year': 1880,
   'driver': {
      'first_name': 'Michael',
      'last_name': 'Schumacher',
      'birth_day': datetime.date(1969, 1, 3),
   },
}
"""

invalid_data = {
    "brand": "Mercedes",
    "production_year": "1990",
    "driver": {"birth_day": "1969-01-03",},
}

deserializer = RaceCarDeserializer(data=invalid_data)
deserializer.is_valid()  # False
deserializer.errors
"""
{
   "model": ["This field is required."],
   "driver": {
      "first_name": ["This field is required."],
      "last_name": ["This field is required."],
   }
}
"""
```

Note that a `Deserializer` is a field too, it can be used the exact same way you use a field (with the [same arguments](https://docs.djangoproject.com/fr/3.0/ref/forms/fields/#core-field-arguments)).

### 3.5. Post-clean methods

A post-clean method is a deserializer's method, specific to a single `Field` and
that will be called once the "standard" validation is done by the deserializer,
allowing you to handle this validated value more easily, then return the value
that will appear in the output data (that will be given to your view).
By convention, their name follows the pattern: `post_clean_<FIELD NAME>`.

For example, if your deserializer defines a `foo` field as a `CharField()`, and
you want that your view receives a custom transformation of that `foo` field (for example, let's
say: striping border spaces), the post-clean method for that field should be
named `post_clean_foo()`:

```python
from flash_rest.deserializers import fields, Deserializer


class FooDeserializer(Deserializer):
   foo = fields.CharField(required=True)

   def post_clean_foo(self, cleaned_value):
      return cleaned_value.strip()
```

**Important Note:** The post-clean methods are called **only** if the field's standard
validation succeeds. If a `ValidationError` occurs, the post-clean won't be
done.

### 3.6 All-pass Deserializer

The `AllPassDeserializer`, is a particular deserializer that allows all payloads to pass to the view, without
any validation: No type-casts, no post-clean methods, and more importantly,
never raises a `ValidationError` or returns a `400 BadRequest`.

The `AllPassDeserializer` is the default deserializer used by `@api_view`
decorator. (You probably won't need it unless you're dealing with a very unusual
use-case)

## 4. Serializers

### 4.1. Introduction

Serializers allow complex data such as querysets and model instances to be
converted into native Python data-types, so that they could be easily rendered
into JSON. Serializers do the opposite of Deserializers, and intervene at the
"return" statement of your view.

### 4.2. Implement a new Serializer

Similar to how we've implemented a `Deserializer`, in order to implement your
own serializer, you have to inherit from `Serializer` class, then define the
fields that you want to include into your serialized data (probably your view's response). Here is a simple
example:

```python
from django.http import JsonResponse

from flash_rest.decorators import api_view
from flash_rest.http import status
from flash_rest.serializers import fields, Serializer

from .models import Subscription


class SubscriptionSerializer(Serializer):
    id = fields.IntegerField(required=True)
    user_id = fields.IntegerField()
    started_at = fields.CharField(attr_name="created")
    invoices_urls = fields.ListField(fields.CharField(required=True))

@api_view
def subscription_details_view(request, url_params, **kwargs):
   subscription = Subscription.objects.get(id=url_params["subscription_pk"])
   return JsonResponse(
      SubscriptionSerializer(subscription, many=False).data,
      status=status.HTTP_200_OK,
   )

```

`Serializer` class accepts 2 arguments:

1. **instance**: The object (or iterable of objects) to be serialized.
2. **many**: Boolean that tells the `Serializer` if the object is iterable or not. If
   `many=True`, the serialized data will be a `list` of serialized elements of
   the `instance` iterable. Its set by default to `False`.

### 4.3. Available Serializer Fields

Serializers fields are very limited, because, remember that the data will be converted
into native Python data-types (that are limited too). Besides primitive fields (`CharField`,
`IntegerField`, `FloatField`, `BooleanField`), django-flash-REST provides 3 additional
fields to use within `Serializers`: `ListField`, `ConstantField` and `MethodField` (and the nested
serializers). Let's dive into existing fields details.

**Note** In order to simplify the wording in this section, "field" word refers
to the serializer's field, and "attribute" word to an attribute of the object
to serialize.

#### 1. Primitive types

The primitive types are serializer's fields that cast your data into Python's
native data-types: `str`, `int`, `float` and `bool`. The `CharField`,
`IntegerField`, `FloatField` and `BooleanField` accept the **same** arguments:

```python
BooleanField(attr_name: str = None, label: str = None, call: bool = False, required: bool = True)
CharField(attr_name: str = None, label: str = None, call: bool = False, required: bool = True)
FloatField(attr_name: str = None, label: str = None, call: bool = False, required: bool = True)
IntegerField(attr_name: str = None, label: str = None, call: bool = False, required: bool = True)
```

1. **attr_name**: It refers to the object's attribute that should be binded to the
   current field. The default value is the field name. For example:

   ```python
   class Example:
       def __init__(self, foo, bar):
          self.foo = foo
          self.bar = bar

   class ExampleSerializer(Serializer):
       foo = fields.IntegerField()  # if `attr_name` is omitted, this field will lookup for your object's `.foo` attribute value
       whatever = fields.CharField(attr_name="bar")  # this field will store your object's `.bar` attribute's value

   ExampleSerializer(Example(foo=3, bar="test")).data  # {'foo': 3, 'whatever': 'test'}
   ```

2. **label**: It's the name you want to give to your field in the serialized object.
   If omitted, it preserves the field's name. For the same `Example` class defined above, let's use `label` attribute:

   ```python

   class ExampleSerializer(Serializer):
       foo = fields.IntegerField(label='integerFoo')
       whatever = fields.CharField(attr_name='bar', label='textBar')

   ExampleSerializer(Example(foo=3, bar="test")).data  # {'integerFoo': 3, 'textBar': 'test'}
   ```

3. **call**: If set to `True`, the serializer will try to execute (call)
   your attribute. This is useful when the attribute referred-to is a method. Here is a quick example:

   ```python
   class Example:
       def __init__(self, foo):
           self.foo = foo

       def _get_text(self):
           return "Hello"

       def bar(self):
           return self._get_text() + " World!"

   class ExampleSerializer(Serializer):
       foo = fields.IntegerField()
       whatever = fields.CharField(attr_name="bar", call=True)  # 'bar' is callable

   ExampleSerializer(Example(foo=3)).data  # {'foo': 3, 'whatever': 'Hello World!'}
   ```

4. **required**: When set to `True`, if the serializer fails to
   retrieve the attribute's value, or to convert it into the target type, a `SerializationError` will be raised.
   If the fields isn't required (`required=False`), in case the serializer fails to render the attribute's value,
   the field won't be added to the final result. If we take the same `Example` class from the previous examples:

   ```python
   class Example:
       def __init__(self, foo, bar):
           self.foo = foo
           self.bar = bar

   class ExampleSerializer(Serializer):
       foo = fields.IntegerField()
       bar = fields.IntegerField(required=True)  # Trying to fit a string into `IntegerField`

   ExampleSerializer(Example(foo=3, bar="test")).data  # raises a `SerializationError`

   class ExampleSerializer(Serializer):
       foo = fields.IntegerField()
       bar = fields.IntegerField(required=False)  # Trying to fit a string into `IntegerField`

   ExampleSerializer(Example(foo=3, bar="test")).data  # {'foo': 3}
   ```

#### 2. MethodField

There are some situations in which you'd need a calculated value (from one or multiple attributes),
without polluting your view, nor your model with a new method.
In that case, `MethodField` could be very useful. By defining a `MethodField`,
you have to define a method in your `Serializer`, that receives your object as
input, and has to return the value to be rendered

**Note** `MethodField` is very similar to a deserializer's post-clean method,
the only difference is that the post-clean receives the attribute's value,
while the `MethodField` receives the whole object.

Here is a simple example that illustrates how `MethodField` works:

```python
from flash_rest.serializers import fields, Serializer

TAX_RATE = 20

class PricingExample:
    def __init__(self, initial_price):
        self.initial_price = initial_price

class PricingSerializer(Serializer):
    initial_price = fields.FloatField()
    final_price = fields.MethodField(method_name="calculate_final_price", required=True)

    def calculate_final_price(self, obj: PricingExample):
        tax_price = obj.initial_price * (TAX_RATE / 100)
        return obj.initial_price + tax_price

PricingSerializer(PricingExample(initial_price=200)).data  # {'initial_price': 200.0, 'final_price': 240.0}
```

`MethodField` accepts 3 arguments:

```python
MethodField(label: str = None, required: bool = True, method_name: str = None)
```

1. **label**: The same as [primitive fields](#1-primitive-types) `label`.
2. **required**: The same as [primitive fields](#1-primitive-types) `label`.
3. **method_name**: The name of the serializer's method that should be
   called. The default value is `get_<Serializer's field name>` (in the previous
   example, if `method_name` was not given, the method should have been renamed
   `get_final_price(self, obj)`)

**Important note:** The `MethodField`'s method should return native Python
data-types (`str`, `bool`, `int`, `float`, `None`) or (nested) `list`/`dict` of native types.

#### 3. ConstantField

`ConstantField` allows you to include constant data in your response, without
having to include that constant in your model. In the previous example,
`TAX_RATE` was a constant. In case we wanted to include it in the serialized
data, we should had defined it as `PricingExample` class/instance attribute, or
created a `MethodField` that returns a constant. Both solutions are quite
"painful". Using `ConstantField`, the code will look like:

```python
from flash_rest.serializers import fields, Serializer

TAX_RATE = 20

class PricingExample:
    def __init__(self, initial_price):
        self.initial_price = initial_price

class PricingSerializer(Serializer):
    initial_price = fields.FloatField()
    final_price = fields.MethodField(method_name="calculate_final_price", required=True)
    tax_rate = fields.ConstantField(constant=TAX_RATE)

    def calculate_final_price(self, obj: PricingExample):
        tax_price = obj.initial_price * (TAX_RATE / 100)
        return obj.initial_price + tax_price

PricingSerializer(PricingExample(initial_price=200)).data  # {'initial_price': 200.0, 'final_price': 240.0, 'tax_rate': 20}
```

`ConstantField` accepts 3 arguments:

```python
ConstantField(label: str = None, required: bool = True, constant: Any = None)
```

1. **label**: The same as [primitive fields](#1-primitive-types) `label`.
2. **required**: The same as [primitive fields](#1-primitive-types) `label`.
3. **constant**: The constant to be included in the serialized object. The
   constant **should be** primitive (i.e. `str`, `bool`, `int`, `float`, `None`
   or combinations -`list`/`dict`- of them), otherwise `SerializationError` will
   be raised (unless `required` is set to `False`, in that case, the field won't figure
   in the rendered object).

#### 4. ListField

`ListField` allows you to serialize iterables of primitives. Let's say your
object's attribute is a list of integers. With a simple `IntegerField`, you
won't be able to serialize that field. It could be achieved with `MethodField`,
but it will be too much written code for a trivial thing. `ListField` does the
same thing as the `many=True` for `Serializer` class, but the `many` argument
isn't implemented for `IntegerField`, `BooleanField`, `FloatField` and
`CharField` for performance purpose.
The `ListField` accepts a single argument which is the field to be rendered as list.

```python
ListField(Union[BooleanField, CharField, FloatField, IntegerField])
```

Here is a simple example:

```python
from flash_rest.serializers import fields, Serializer


class Path:
   def __init__(self):
      self.x_coordinates = [1.0, 1.2, 1.5, 1.8, 2.3, 8.6]
      self.y_coordinates = [19.0, 20.9, 30.1, 15.0, 22.3, 5.0]


class PathSerializer(Serializer):
   xs = fields.ListField(
      fields.FloatField(label='path_xs', attr_name='x_coordinates', required=True)
   )
   ys = fields.ListField(
      fields.FloatField(label='path_ys', attr_name='y_coordinates', required=True)
   )

PathSerializer(Path()).data  # {'path_xs': [1.0, 1.2, 1.5, 1.8, 2.3, 8.6], 'path_ys': [19.0, 20.9, 30.1, 15.0, 22.3, 5.0]}
```

### 4.4. Nested Serializers

Similarly to `Deserializer`, `Serializer` sub-classes could be nested (i.e.
using `Serializer` sub-class as a serializer's field). Here is a simple example
that shows how to nest serializers:

```python
from datetime import datetime

from flash_rest.serializers import fields, Serializer


class Invoice:
    def __init__(self, id, date):
        self.id = id
        self.created_at = date


class Subscription:
    def __init__(self):
        self.name = "foo bar subscription"
        self.invoices = [Invoice(id=i, date=datetime.now()) for i in range(10)]


class InvoiceSerializer(Serializer):
    id = fields.IntegerField()
    created = fields.CharField(attr_name="created_at")


class SubscriptionSerializer(Serializer):
    name = fields.CharField()
    invoices = InvoiceSerializer(many=True)


SubscriptionSerializer(instance=Subscription()).data  # {'name': 'foo bar subscription', 'invoices': [{'id': 0, 'created': '2020-06-08 15:26:15.414524'}, ..., {'id': 9, '2020-06-08 15:26:15.93843'}]}
```

### 4.5. DictSerializer

A `DictSerializer` is a sub-class of `Serializer` (it means that it's
a particular serializer), that, instead of taking an object (class
instance) as input, it takes a `dict`. The `DictSerializer` transforms a `dict`
into another `dict`. It accepts the same fields as the classic serializer.
Here is the previous example, rewritten using `DictSerializer` (to show the
difference):

```python
from datetime import datetime

from flash_rest.serializers import fields, DictSerializer


subscription = {
    "name": "foo bar subscription",
    "invoices": [
        {"id": 0, "created_at": "2020-06-08 15:26:15.414524"},
        {"id": 9, "created_at": "2020-06-08 15:26:15.93843"},
    ],
}


class InvoiceSerializer(DictSerializer):
    id = fields.IntegerField()
    created = fields.CharField(attr_name="created_at")


class SubscriptionSerializer(DictSerializer):
    name = fields.CharField()
    invoices = InvoiceSerializer(many=True)


SubscriptionSerializer(instance=subscription).data  # {'name': 'foo bar subscription', 'invoices': [{'id': 0, 'created': '2020-06-08 15:26:15.414524'}, ..., {'id': 9, '2020-06-08 15:26:15.93843'}]}
```

## 5. Exceptions

### 5.1. `@api_view` exceptions catching

The `@api_view` decorator catches exceptions for you in case you did not, and returns a JSON response with the correct status code.
If the raised exception is a sub-class of `flash_rest.http.exceptions.BaseAPIException`, a custom message and status code will be returned.
If it's not the case, the returned JSON response will have `"An unknown server error occured."` as message, and `500` as status code.

By raising one of the [existing API exceptions](#52-existing-api-exceptions) (or
[defining your own](#53-define-your-own-api-exception)), the decorator will
return the response with the correct message (and status code). This approach
ensures that:

1. Your responses are standardized in all your decorated views: always the same message and status code for the same situations.
2. Your view's code is lighter (dropping all the useless `try/except` clauses).

Here is a simple example of a view that receives `url_params`, calls a `find_results()` function, and returns a `404` in case there is no result:

```python
from flash_rest.decorators import api_view
from flash_rest.http.exceptions import NotFound

@api_view
def user_custom_view(request, url_params, **kwargs):
    results = find_results(**url_params)
    if results is None or len(results) == 0:
        raise NotFound

    # In case the `find_results()` returned non-empty results:
    # [....]
```

### 5.2. Existing API Exceptions

As seen in the previous chapter, django-flash-REST provides you some custom exceptions that you can use (_i.e._ raise) so that your view returns an error response,
without having to do it manually everytime. Here is the list of the available API exceptions , each with its returned object and status code:

-  **BadRequest**:

   Response message: _"Bad request."_ - status code: `400`

-  **NotAuthenticated**:

   Response message: _"Unauthorized operation. Maybe forgot the authentication step ?"_ - status code: `401`

-  **PermissionDenied**:

   Response message: _"Forbidden operation. Make sure you have the right permissions."_ - status code: `403`

-  **NotFound**:

   Response message: _"The requested resource is not found."_ - status code: `404`

-  **MethodNotAllowed**:

   Response message: _"HTTP Method not allowed."_ - status code: `405`

-  **UnsupportedMediaType**:

   Response message: _"Unsupported Media Type. Check your request's Content-Type."_ - status code: `415`

*  **InternalServerError**:

   Response message: _"An unknown server error occured."_ - status code: `500`

*  **ServiceUnavailable**:

   Response message: _"The requested service is unavailable."_ - status code: `502`

### 5.3. Define your own API Exception

In order to define your own API Exception, all you have to do is inheriting from
`flash_rest.http.exceptions.BaseAPIException` (or one of its sub-classes), then override its `STATUS_CODE` and `RESPONSE_MESSAGE` attributes.

Here is a simple example that shows how to define a [conflict](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/409) exception:

```python
from flash_rest.decorators import api_view
from flash_rest.http import exceptions, status

class Conflict(exceptions.BaseAPIException):
    STATUS_CODE = status.HTTP_409_CONFLICT
    RESPONSE_MESSAGE = "Requests conflict."

@api_view
def my_conflicting_view(request, **kwargs):
    # [...]
    if some_condition_is_satisfied:
        raise Conflict  # returns JsonResponse({'error_msg': 'Requests conflict.'}, status=409)
    # [....]
```

## 6. HTTP

django-flash-REST provides some constants/enumerations that allow you to avoid using
hard-coded values (`str` for HTTP methods, and `int` for status codes), and
improve your code readability.

### 6.1. HTTP Status codes

The HTTP status codes can be imported from `flash_rest.http.status`:

```python
from flash_rest.http.status import HTTP_200_OK

response_status = HTTP_200_OK

# OR
from flash_rest.http import status

response_status = status.HTTP_200_OK

```

Here is the exhaustive list of http status constants provided by django-flash-REST
(more details about status codes [here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)):

-  `HTTP_100_CONTINUE`
-  `HTTP_101_SWITCHING_PROTOCOLS`
-  `HTTP_200_OK`
-  `HTTP_201_CREATED`
-  `HTTP_202_ACCEPTED`
-  `HTTP_203_NON_AUTHORITATIVE_INFORMATION`
-  `HTTP_204_NO_CONTENT`
-  `HTTP_205_RESET_CONTENT`
-  `HTTP_206_PARTIAL_CONTENT`
-  `HTTP_207_MULTI_STATUS`
-  `HTTP_208_ALREADY_REPORTED`
-  `HTTP_226_IM_USED`
-  `HTTP_300_MULTIPLE_CHOICES`
-  `HTTP_301_MOVED_PERMANENTLY`
-  `HTTP_302_FOUND`
-  `HTTP_303_SEE_OTHER`
-  `HTTP_304_NOT_MODIFIED`
-  `HTTP_305_USE_PROXY`
-  `HTTP_306_RESERVED`
-  `HTTP_307_TEMPORARY_REDIRECT`
-  `HTTP_308_PERMANENT_REDIRECT`
-  `HTTP_400_BAD_REQUEST`
-  `HTTP_401_UNAUTHORIZED`
-  `HTTP_402_PAYMENT_REQUIRED`
-  `HTTP_403_FORBIDDEN`
-  `HTTP_404_NOT_FOUND`
-  `HTTP_405_METHOD_NOT_ALLOWED`
-  `HTTP_406_NOT_ACCEPTABLE`
-  `HTTP_407_PROXY_AUTHENTICATION_REQUIRED`
-  `HTTP_408_REQUEST_TIMEOUT`
-  `HTTP_409_CONFLICT`
-  `HTTP_410_GONE`
-  `HTTP_411_LENGTH_REQUIRED`
-  `HTTP_412_PRECONDITION_FAILED`
-  `HTTP_413_REQUEST_ENTITY_TOO_LARGE`
-  `HTTP_414_REQUEST_URI_TOO_LONG`
-  `HTTP_415_UNSUPPORTED_MEDIA_TYPE`
-  `HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE`
-  `HTTP_417_EXPECTATION_FAILED`
-  `HTTP_418_IM_A_TEAPOT`
-  `HTTP_422_UNPROCESSABLE_ENTITY`
-  `HTTP_423_LOCKED`
-  `HTTP_424_FAILED_DEPENDENCY`
-  `HTTP_426_UPGRADE_REQUIRED`
-  `HTTP_428_PRECONDITION_REQUIRED`
-  `HTTP_429_TOO_MANY_REQUESTS`
-  `HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE`
-  `HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS`
-  `HTTP_500_INTERNAL_SERVER_ERROR`
-  `HTTP_501_NOT_IMPLEMENTED`
-  `HTTP_502_BAD_GATEWAY`
-  `HTTP_503_SERVICE_UNAVAILABLE`
-  `HTTP_504_GATEWAY_TIMEOUT`
-  `HTTP_505_HTTP_VERSION_NOT_SUPPORTED`
-  `HTTP_506_VARIANT_ALSO_NEGOTIATES`
-  `HTTP_507_INSUFFICIENT_STORAGE`
-  `HTTP_508_LOOP_DETECTED`
-  `HTTP_509_BANDWIDTH_LIMIT_EXCEEDED`
-  `HTTP_510_NOT_EXTENDED`
-  `HTTP_511_NETWORK_AUTHENTICATION_REQUIRED`

Besides, you also have (in the same module `flash_rest.http.status`) 5 functions that you can use to verify
a status code category easily:

-  `is_informational(code: int) -> bool`
-  `is_success(code: int) -> bool`
-  `is_redirect(code: int) -> bool`
-  `is_client_error(code: int) -> bool`
-  `is_server_error(code: int) -> bool`

### 6.2. HTTP Methods

All the following HTTP method's related constants can be found in
`flash_rest.http.methods`:

**String constants:**

-  `HEAD`
-  `GET`
-  `POST`
-  `PUT`
-  `PATCH`
-  `DELETE`
-  `OPTIONS`
-  `TRACE`
-  `CONNECT`

**Tuple constants:**

-  `SAFE_METHODS` = (`GET`, `HEAD`, `OPTIONS`)
-  `SUPPORTING_PAYLOAD_METHODS` = (`POST`, `PUT`, `PATCH`)
-  `ALL_METHODS` = (`HEAD`, `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`, `TRACE`, `CONNECT`)

<p align="center">&mdash; Made with :hearts: &mdash;</p>

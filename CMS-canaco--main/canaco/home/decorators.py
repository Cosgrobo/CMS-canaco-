from django.contrib.auth.decorators import user_passes_test


def es_operador(user):
    return (
        user.is_authenticated
        and user.is_staff
        and user.is_active
    )


def operador_required(view_func):
    return user_passes_test(
        es_operador,
        login_url='home:login'
    )(view_func)
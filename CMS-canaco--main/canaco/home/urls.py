
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from . import views

app_name = "home"

urlpatterns = [

    # ==========================================
    # PÁGINAS PRINCIPALES
    # ==========================================

    path("", views.index, name="index"),
    path("base/", views.base, name="base"),
    path("contactanos/", views.contactanos, name="contactanos"),

    # Categorías públicas
    path("categoria/", views.categoria, name="categoria"),
    path(
        "categoria/<int:pk>/",
        views.categoria_detalle,
        name="categoria_detalle"
    ),

    # ==========================================
    # AUTENTICACIÓN
    # ==========================================

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="home/login.html"
        ),
        name="login"
    ),

    path(
        "logout/",
        LogoutView.as_view(next_page="home:index"),
        name="logout"
    ),

    path("sign_up/", views.sign_up, name="sign_up"),

    # ==========================================
    # NOTICIAS
    # ==========================================

    path("noticia/", views.noticia, name="noticia"),

    path(
        "noticia/<int:publicacion_id>/",
        views.noticia,
        name="noticia_detalle"
    ),
    # Crear noticia
    path(
        "crear_publicacion/",
        views.crear_publicacion,
        name="crear_publicacion"
    ),

    # CRUD de noticias
    path(
        "crud_noticias/",
        views.crud_noticias,
        name="crud_noticias"
    ),

    # Mantener compatibilidad con la ruta anterior
    path(
        "crud_noticas/",
        views.crud_noticas,
        name="crud_noticas"
    ),

    path(
        "crud_noticias/<int:pk>/editar/",
        views.editar_publicacion,
        name="editar_publicacion"
    ),

    path(
        "crud_noticias/<int:pk>/publicar/",
        views.publicar_publicacion,
        name="publicar_publicacion"
    ),

    path(
        "crud_noticias/<int:pk>/eliminar/",
        views.eliminar_publicacion,
        name="eliminar_publicacion"
    ),

    # ==========================================
    # COMENTARIOS
    # ==========================================

    path(
        "crud_comentarios/",
        views.crud_comentarios,
        name="crud_comentarios"
    ),

    path(
        "crud_comentarios/<int:pk>/aprobar/",
        views.aprobar_comentario,
        name="aprobar_comentario"
    ),

    path(
        "crud_comentarios/<int:pk>/bloquear/",
        views.bloquear_comentario,
        name="bloquear_comentario"
    ),

    path(
        "crud_comentarios/<int:pk>/eliminar/",
        views.eliminar_comentario,
        name="eliminar_comentario"
    ),

    # ==========================================
    # CATEGORÍAS
    # ==========================================

    path(
        "crud_categorias/",
        views.crud_categorias,
        name="crud_categorias"
    ),

    path(
        "crud_categorias/<int:pk>/editar/",
        views.editar_categoria,
        name="editar_categoria"
    ),

    path(
        "crud_categorias/<int:pk>/eliminar/",
        views.eliminar_categoria,
        name="eliminar_categoria"
    ),

    # Se conserva la ruta anterior sin identificador
    path(
        "editar_categoria/",
        views.editar_categoria,
        name="editar_categoria_sin_pk"
    ),

    # ==========================================
    # PERFIL
    # ==========================================

    path("perfil/", views.perfil, name="perfil"),

    path(
        "crud_perfil/",
        views.crud_perfil,
        name="crud_perfil"
    ),

    path(
        "crud_cambiar_contrasena/",
        views.crud_cambiar_contrasena,
        name="crud_cambiar_contrasena"
    ),

    # ==========================================
    # USUARIOS
    # ==========================================

    path(
        "crear_usuario/",
        views.crear_usuario,
        name="crear_usuario"
    ),

    path(
        "crud_usuarios/",
        views.crud_usuarios,
        name="crud_usuarios"
    ),

    path(
        "crud_usuarios/<int:pk>/editar/",
        views.editar_usuario,
        name="editar_usuario"
    ),

    path(
        "crud_usuarios/<int:pk>/bloquear/",
        views.bloquear_usuario,
        name="bloquear_usuario"
    ),

    path(
        "crud_usuarios/<int:pk>/eliminar/",
        views.eliminar_usuario,
        name="eliminar_usuario"
    ),

]

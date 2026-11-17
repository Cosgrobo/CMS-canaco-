import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F
from django.db.models.deletion import RestrictedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash

from .decorators import operador_required
from .models import (
    Archivo,
    Categoria,
    Comentario,
    GaleriaPublicacion,
    Perfil,
    Publicacion,
)


# ==========================================
# INICIO
# ==========================================

def index(request):
    publicaciones_publicadas = Publicacion.objects.filter(
        estado=Publicacion.ESTADO_PUBLICADO
    ).select_related('categoria', 'imagen_portada')

    noticias = publicaciones_publicadas.order_by('-createdat')[:4]
    noticias_mas_vistas = publicaciones_publicadas.order_by('-visitas', '-createdat')[:4]
    ids_noticias_recientes = list(noticias.values_list('pk', flat=True))
    lista_noticias = publicaciones_publicadas.exclude(
        pk__in=ids_noticias_recientes
    ).order_by('-createdat')

    return render(request, 'home/index.html', {
        'noticias': noticias,
        'noticias_mas_vistas': noticias_mas_vistas,
        'lista_noticias': lista_noticias,
    })


def base(request):
    return render(request, 'home/base.html')


def contactanos(request):
    return render(request, 'home/contactanos.html')


# ==========================================
# CATEGORÍAS: LISTADO PÚBLICO
# ==========================================

def categoria(request):
    categorias = Categoria.objects.annotate(
        publicaciones_count=Count('publicacion')
    ).order_by('nombre')

    publicaciones = (
        Publicacion.objects.filter(
            estado=Publicacion.ESTADO_PUBLICADO
        )
        .select_related('categoria', 'imagen_portada')
        .order_by('-createdat')
    )

    categoria_id = request.GET.get('categoria', '')
    categoria_seleccionada = None

    if categoria_id.isdigit():
        categoria_seleccionada = categorias.filter(
            pk=int(categoria_id)
        ).first()

        if categoria_seleccionada:
            publicaciones = publicaciones.filter(
                categoria=categoria_seleccionada
            )

    page_obj = Paginator(
        publicaciones, 10
    ).get_page(request.GET.get('page'))

    publicaciones_recientes = (
        Publicacion.objects.filter(
            estado=Publicacion.ESTADO_PUBLICADO
        )
        .select_related('categoria', 'imagen_portada')
        .order_by('-createdat')[:4]
    )

    return render(
        request,
        'home/categoria.html',
        {
            'categorias': categorias,
            'categoria_seleccionada': categoria_seleccionada,
            'page_obj': page_obj,
            'publicaciones_recientes': publicaciones_recientes,
        }
    )


# ==========================================
# DETALLE DE NOTICIA
# ==========================================

def noticia(request, publicacion_id=None):

    publicaciones = Publicacion.objects.select_related(
        'autor',
        'categoria',
        'imagen_portada'
    ).order_by('-createdat')

    # Los operadores pueden consultar borradores.
    # Los visitantes solamente pueden consultar noticias publicadas.
    if not (
        request.user.is_authenticated
        and request.user.is_staff
        and request.user.is_active
    ):
        publicaciones = publicaciones.filter(
            estado=Publicacion.ESTADO_PUBLICADO
        )

    if publicacion_id is not None:
        publicacion = get_object_or_404(
            publicaciones,
            pk=publicacion_id
        )
    else:
        publicacion = publicaciones.first()

    contexto = {
        'publicacion': publicacion,
        'galeria': [],
        'comentarios': [],
        'publicaciones_relacionadas': [],
        'noticia_anterior': None,
        'noticia_siguiente': None,
    }

    if publicacion:

        # Incrementar visitas.
        Publicacion.objects.filter(
            pk=publicacion.pk
        ).update(
            visitas=F('visitas') + 1
        )

        publicacion.refresh_from_db()

        # Registrar comentarios.
        if request.method == 'POST':

            if not request.user.is_authenticated:
                messages.error(
                    request,
                    'Inicia sesión para comentar.'
                )
                return redirect('home:login')

            contenido = request.POST.get(
                'contenido', ''
            ).strip()

            if contenido:
                Comentario.objects.create(
                    contenido=contenido,
                    estado=Comentario.ESTADO_PENDIENTE,
                    publicacion=publicacion,
                    user=request.user,
                )

                messages.success(
                    request,
                    'Tu comentario se envió para revisión.'
                )

                return redirect(
                    'home:noticia_detalle',
                    publicacion_id=publicacion.pk
                )

            messages.error(
                request,
                'Escribe un comentario antes de enviarlo.'
            )

        relacionadas = publicaciones.exclude(
            pk=publicacion.pk
        )

        if publicacion.categoria_id:
            relacionadas = relacionadas.filter(
                categoria_id=publicacion.categoria_id
            )

        contexto.update({
            'galeria': GaleriaPublicacion.objects.filter(
                publicacion=publicacion
            ).select_related('archivo'),

            'comentarios': Comentario.objects.filter(
                publicacion=publicacion,
                estado=Comentario.ESTADO_APROBADO,
            ).select_related(
                'user'
            ).order_by('createdat'),

            'publicaciones_relacionadas': list(
                relacionadas[:3]
            ),

            'noticia_anterior': publicaciones.filter(
                pk__gt=publicacion.pk
            ).order_by('pk').first(),

            'noticia_siguiente': publicaciones.filter(
                pk__lt=publicacion.pk
            ).order_by('-pk').first(),
        })

    return render(
        request,
        'home/noticia.html',
        contexto
    )


# ==========================================
# REGISTRO DE USUARIOS
# ==========================================

def sign_up(request):

    if request.method == 'POST':

        username = request.POST.get(
            'username', ''
        ).strip()

        email = request.POST.get(
            'email', ''
        ).strip()

        first_name = request.POST.get(
            'first_name', ''
        ).strip()

        apellido_paterno = request.POST.get(
            'apellido_paterno', ''
        ).strip()

        apellido_materno = request.POST.get(
            'apellido_materno', ''
        ).strip()

        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(
                request,
                'Las contraseñas no coinciden.'
            )
            return redirect('home:sign_up')

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                'El nombre de usuario ya existe.'
            )
            return redirect('home:sign_up')

        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                'El correo electrónico ya está registrado.'
            )
            return redirect('home:sign_up')

        usuario = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        usuario.first_name = first_name

        usuario.last_name = (
            f'{apellido_paterno} {apellido_materno}'
        ).strip()

        usuario.save()

        perfil_usuario, creado = Perfil.objects.get_or_create(
            user=usuario
        )

        perfil_usuario.apellido_paterno = apellido_paterno
        perfil_usuario.apellido_materno = apellido_materno
        perfil_usuario.save()

        messages.success(
            request,
            'Tu cuenta se creó correctamente. Ahora puedes iniciar sesión.'
        )

        return redirect('home:login')

    return render(request, 'home/sign_up.html')


# ==========================================
# PERFIL
# ==========================================

@login_required
def perfil(request):

    perfil_usuario, _ = Perfil.objects.get_or_create(
        user=request.user
    )

    recuperar_foto_perfil(
        perfil_usuario,
        request.user
    )

    return render(
        request,
        'home/perfil.html',
        {
            'perfil_usuario': perfil_usuario
        }
    )


# ==========================================
# CREAR PUBLICACIÓN
# ==========================================

@operador_required
def crear_publicacion(request):

    categorias = Categoria.objects.order_by('nombre')

    if request.method == 'POST':

        titulo = request.POST.get(
            'titulo', ''
        ).strip()

        resumen = request.POST.get(
            'resumen', ''
        ).strip()

        contenido = request.POST.get(
            'contenido', ''
        ).strip()

        categoria_id = request.POST.get('categoria')

        estado = request.POST.get(
            'estado',
            Publicacion.ESTADO_BORRADOR
        )

        if not titulo or not resumen or not contenido:

            messages.error(
                request,
                'Completa el título, resumen y contenido.'
            )

            return render(
                request,
                'home/crear_publicacion.html',
                {
                    'categorias': categorias,
                }
            )

        categoria_obj = None

        if categoria_id:
            categoria_obj = get_object_or_404(
                Categoria,
                pk=categoria_id
            )

        if estado not in (
            Publicacion.ESTADO_BORRADOR,
            Publicacion.ESTADO_PUBLICADO,
        ):
            estado = Publicacion.ESTADO_BORRADOR

        publicacion = Publicacion.objects.create(
            titulo=titulo,
            resumen=resumen,
            contenido=contenido,
            estado=estado,
            visitas=0,
            autor=request.user,
            categoria=categoria_obj,
        )

        portada = request.FILES.get('imagen_portada')

        if portada:
            publicacion.imagen_portada = guardar_archivo(
                portada,
                request.user
            )

            publicacion.save(
                update_fields=['imagen_portada']
            )

        for archivo in request.FILES.getlist('galeria'):

            archivo_guardado = guardar_archivo(
                archivo,
                request.user
            )

            GaleriaPublicacion.objects.create(
                archivo=archivo_guardado,
                publicacion=publicacion,
            )

        messages.success(
            request,
            'La noticia se creó correctamente.'
        )

        return redirect('home:crud_noticias')

    return render(
        request,
        'home/crear_publicacion.html',
        {
            'categorias': categorias,
        }
    )


def crear_usuario(request):
    return render(request, 'home/crear_usuario.html')


# ==========================================
# CAMBIAR CONTRASEÑA
# ==========================================

@login_required
def crud_cambiar_contrasena(request):

    if request.method == 'POST':

        actual = request.POST.get('actual')
        nueva = request.POST.get('nueva')
        confirmar = request.POST.get('confirmar')

        user = request.user

        if not user.check_password(actual):
            messages.error(
                request,
                'La contraseña actual es incorrecta.'
            )
            return redirect('home:crud_cambiar_contrasena')

        if not nueva:
            messages.error(
                request,
                'La nueva contraseña no puede estar vacía.'
            )
            return redirect('home:crud_cambiar_contrasena')

        if nueva != confirmar:
            messages.error(
                request,
                'Las contraseñas nuevas no coinciden.'
            )
            return redirect('home:crud_cambiar_contrasena')

        user.set_password(nueva)
        user.save()

        update_session_auth_hash(
            request,
            user
        )

        messages.success(
            request,
            'Tu contraseña se actualizó correctamente.'
        )

        return redirect('home:perfil')

    return render(
        request,
        'home/crud_cambiar_contrasena.html'
    )


# ==========================================
# CRUD DE CATEGORÍAS
# ==========================================

@operador_required
def crud_categorias(request):

    if request.method == 'POST':

        nombre = request.POST.get(
            'nombre', ''
        ).strip()

        if not nombre:

            messages.error(
                request,
                'Escribe el nombre de la categoría.'
            )

        elif Categoria.objects.filter(
            nombre__iexact=nombre
        ).exists():

            messages.error(
                request,
                'Ya existe una categoría con ese nombre.'
            )

        else:

            Categoria.objects.create(
                nombre=nombre,
                fk_user=request.user
            )

            messages.success(
                request,
                'Categoría creada correctamente.'
            )

        return redirect('home:crud_categorias')

    categorias = Categoria.objects.order_by(
        '-createdat'
    )

    return render(
        request,
        'home/crud_categorias.html',
        {
            'categorias': categorias,
        }
    )


@operador_required
def editar_categoria(request, pk=None):

    if pk is None:
        return redirect('home:crud_categorias')

    categoria_obj = get_object_or_404(
        Categoria,
        pk=pk
    )

    if request.method == 'POST':

        nombre = request.POST.get(
            'nombre', ''
        ).strip()

        if not nombre:

            messages.error(
                request,
                'El nombre de la categoría es obligatorio.'
            )

        elif Categoria.objects.filter(
            nombre__iexact=nombre
        ).exclude(pk=pk).exists():

            messages.error(
                request,
                'Ya existe otra categoría con ese nombre.'
            )

        else:

            categoria_obj.nombre = nombre
            categoria_obj.updatedat = timezone.now()
            categoria_obj.save()

            messages.success(
                request,
                'Categoría actualizada correctamente.'
            )

            return redirect('home:crud_categorias')

    return render(
        request,
        'home/editar_categoria.html',
        {
            'categoria': categoria_obj,
        }
    )


@operador_required
def eliminar_categoria(request, pk):

    if request.method != 'POST':
        return redirect('home:crud_categorias')

    categoria_obj = get_object_or_404(
        Categoria,
        pk=pk
    )

    try:
        categoria_obj.delete()

    except RestrictedError:

        messages.error(
            request,
            'No se puede eliminar esta categoría porque tiene noticias asociadas.'
        )

    else:

        messages.success(
            request,
            'Categoría eliminada correctamente.'
        )

    return redirect('home:crud_categorias')


# ==========================================
# CRUD DE COMENTARIOS
# ==========================================

@operador_required
def crud_comentarios(request):

    comentarios = Comentario.objects.select_related(
        'publicacion',
        'user'
    ).order_by('-createdat')

    return render(
        request,
        'home/crud_comentarios.html',
        {
            'comentarios': comentarios,
        }
    )


@operador_required
def aprobar_comentario(request, pk):

    if request.method == 'POST':

        comentario = get_object_or_404(
            Comentario,
            pk=pk
        )

        comentario.estado = Comentario.ESTADO_APROBADO

        comentario.save(
            update_fields=['estado', 'updatedat']
        )

        messages.success(
            request,
            'Comentario aprobado correctamente.'
        )

    return redirect('home:crud_comentarios')


@operador_required
def bloquear_comentario(request, pk):

    if request.method == 'POST':

        comentario = get_object_or_404(
            Comentario,
            pk=pk
        )

        comentario.estado = Comentario.ESTADO_BLOQUEADO

        comentario.save(
            update_fields=['estado', 'updatedat']
        )

        messages.success(
            request,
            'Comentario bloqueado correctamente.'
        )

    return redirect('home:crud_comentarios')


@operador_required
def eliminar_comentario(request, pk):

    if request.method == 'POST':

        comentario = get_object_or_404(
            Comentario,
            pk=pk
        )

        comentario.delete()

        messages.success(
            request,
            'Comentario eliminado correctamente.'
        )

    return redirect('home:crud_comentarios')


# ==========================================
# CRUD DE NOTICIAS
# ==========================================

@operador_required
def crud_noticias(request):

    publicaciones = Publicacion.objects.select_related(
        'categoria',
        'autor'
    ).order_by('-createdat')

    return render(
        request,
        'home/crud_noticias.html',
        {
            'publicaciones': publicaciones,
        }
    )


# Compatibilidad con la ruta anterior que tenía un error tipográfico.
crud_noticas = crud_noticias


@operador_required
def editar_publicacion(request, pk):

    publicacion = get_object_or_404(
        Publicacion,
        pk=pk
    )

    categorias = Categoria.objects.order_by('nombre')

    if request.method == 'POST':

        titulo = request.POST.get(
            'titulo', ''
        ).strip()

        resumen = request.POST.get(
            'resumen', ''
        ).strip()

        contenido = request.POST.get(
            'contenido', ''
        ).strip()

        categoria_id = request.POST.get('categoria')

        estado = request.POST.get(
            'estado',
            publicacion.estado
        )

        if not titulo or not resumen or not contenido:

            messages.error(
                request,
                'Completa el título, resumen y contenido.'
            )

        else:

            publicacion.titulo = titulo
            publicacion.resumen = resumen
            publicacion.contenido = contenido

            if categoria_id:

                publicacion.categoria = get_object_or_404(
                    Categoria,
                    pk=categoria_id
                )

            else:

                publicacion.categoria = None

            if estado in (
                Publicacion.ESTADO_BORRADOR,
                Publicacion.ESTADO_PUBLICADO,
            ):

                publicacion.estado = estado

            portada = request.FILES.get('imagen_portada')

            if portada:

                publicacion.imagen_portada = guardar_archivo(
                    portada,
                    request.user
                )

            publicacion.save()

            for archivo in request.FILES.getlist('galeria'):

                archivo_guardado = guardar_archivo(
                    archivo,
                    request.user
                )

                GaleriaPublicacion.objects.create(
                    archivo=archivo_guardado,
                    publicacion=publicacion,
                )

            messages.success(
                request,
                'Noticia actualizada correctamente.'
            )

            return redirect('home:crud_noticias')

    return render(
        request,
        'home/editar_publicacion.html',
        {
            'publicacion': publicacion,
            'categorias': categorias,
        }
    )


@operador_required
def publicar_publicacion(request, pk):

    if request.method != 'POST':
        return redirect('home:crud_noticias')

    publicacion = get_object_or_404(
        Publicacion,
        pk=pk
    )

    if publicacion.estado == Publicacion.ESTADO_PUBLICADO:

        publicacion.estado = Publicacion.ESTADO_BORRADOR

        mensaje = 'La noticia se cambió a borrador.'

    else:

        publicacion.estado = Publicacion.ESTADO_PUBLICADO

        mensaje = 'La noticia se publicó correctamente.'

    publicacion.save(
        update_fields=['estado', 'updatedat']
    )

    messages.success(
        request,
        mensaje
    )

    return redirect('home:crud_noticias')


@operador_required
def eliminar_publicacion(request, pk):

    if request.method != 'POST':
        return redirect('home:crud_noticias')

    publicacion = get_object_or_404(
        Publicacion,
        pk=pk
    )

    try:

        with transaction.atomic():

            Comentario.objects.filter(
                publicacion=publicacion
            ).delete()

            GaleriaPublicacion.objects.filter(
                publicacion=publicacion
            ).delete()

            publicacion.delete()

    except RestrictedError:

        messages.error(
            request,
            'No se pudo eliminar la noticia porque tiene otros registros asociados.'
        )

    else:

        messages.success(
            request,
            'Noticia eliminada correctamente.'
        )

    return redirect('home:crud_noticias')


# ==========================================
# DETALLE DE CATEGORÍA
# ==========================================

def categoria_detalle(request, pk):

    categoria_obj = get_object_or_404(
        Categoria,
        pk=pk
    )

    publicaciones = Publicacion.objects.filter(
        categoria=categoria_obj,
        estado=Publicacion.ESTADO_PUBLICADO,
    ).select_related(
        'categoria',
        'imagen_portada',
        'autor'
    ).order_by('-createdat')

    page_obj = Paginator(
        publicaciones,
        10
    ).get_page(request.GET.get('page'))

    return render(
        request,
        'home/categoria.html',
        {
            'categorias': Categoria.objects.annotate(
                publicaciones_count=Count('publicacion')
            ).order_by('nombre'),

            'categoria_seleccionada': categoria_obj,

            'page_obj': page_obj,

            'publicaciones_recientes': Publicacion.objects.filter(
                estado=Publicacion.ESTADO_PUBLICADO
            ).select_related(
                'categoria',
                'imagen_portada'
            ).order_by('-createdat')[:4],
        }
    )


# ==========================================
# CRUD DE USUARIOS
# ==========================================

@operador_required
def crud_usuarios(request):

    for usuario in User.objects.all():

        Perfil.objects.get_or_create(
            user=usuario
        )

    usuarios = User.objects.select_related(
        'perfil'
    ).order_by('date_joined')

    return render(
        request,
        'home/crud_usuarios.html',
        {
            'usuarios': usuarios
        }
    )


# ==========================================
# CRUD DE PERFIL
# ==========================================

@login_required
def crud_perfil(request):

    user = request.user

    perfil, _ = Perfil.objects.get_or_create(
        user=user
    )

    recuperar_foto_perfil(
        perfil,
        user
    )

    if request.method == 'POST':

        username = request.POST.get(
            'username', ''
        ).strip()

        email = request.POST.get(
            'email', ''
        ).strip()

        first_name = request.POST.get(
            'first_name', ''
        ).strip()

        apellido_paterno = request.POST.get(
            'apellido_paterno', ''
        ).strip()

        apellido_materno = request.POST.get(
            'apellido_materno', ''
        ).strip()

        foto = request.FILES.get('foto')

        if not username:

            messages.error(
                request,
                'El nombre de usuario es obligatorio.'
            )

            return redirect('home:crud_perfil')

        if User.objects.filter(
            username=username
        ).exclude(pk=user.pk).exists():

            messages.error(
                request,
                'Este nombre de usuario ya está registrado.'
            )

            return redirect('home:crud_perfil')

        user.username = username
        user.email = email
        user.first_name = first_name

        user.last_name = (
            f'{apellido_paterno} {apellido_materno}'
        ).strip()

        user.save()

        perfil.apellido_paterno = apellido_paterno
        perfil.apellido_materno = apellido_materno

        if foto:

            archivo = guardar_archivo(
                foto,
                user
            )

            perfil.foto_perfil = archivo

        perfil.save()

        messages.success(
            request,
            'Tu perfil se actualizó correctamente.'
        )

        return redirect('home:perfil')

    return render(
        request,
        'home/crud_perfil.html',
        {
            'perfil_usuario': perfil
        }
    )


# ==========================================
# GUARDAR ARCHIVOS
# ==========================================

def guardar_archivo(archivo, user):

    nombre_original = archivo.name

    nombre_temporal = (
        f"{slugify(os.path.splitext(nombre_original)[0])}"
        f"-{timezone.now().timestamp()}"
        f"{os.path.splitext(nombre_original)[1]}"
    )

    nuevo_archivo = Archivo.objects.create(
        nombre=nombre_original,
        nombre_temporal=nombre_temporal,
        ruta=archivo,
        tipo=archivo.content_type or '',
        tamano=archivo.size,
        fk_user=user
    )

    return nuevo_archivo


# ==========================================
# RECUPERAR FOTO DE PERFIL
# ==========================================

def recuperar_foto_perfil(perfil, user):

    """Asocia al perfil la última foto subida que quedó sin vincular."""

    if perfil.foto_perfil_id:
        return

    archivo = (
        Archivo.objects
        .filter(fk_user=user)
        .exclude(ruta='')
        .order_by('-createdat', '-pk')
        .first()
    )

    if archivo:

        perfil.foto_perfil = archivo

        perfil.save(
            update_fields=['foto_perfil']
        )


# ==========================================
# EDITAR USUARIO
# ==========================================

@operador_required
def editar_usuario(request, pk):

    usuario = get_object_or_404(
        User,
        pk=pk
    )

    perfil, _ = Perfil.objects.get_or_create(
        user=usuario
    )

    if request.method == 'POST':

        username = request.POST.get(
            'username', ''
        ).strip()

        email = request.POST.get(
            'email', ''
        ).strip()

        first_name = request.POST.get(
            'first_name', ''
        ).strip()

        apellido_paterno = request.POST.get(
            'apellido_paterno', ''
        ).strip()

        apellido_materno = request.POST.get(
            'apellido_materno', ''
        ).strip()

        rol = request.POST.get('rol')

        if not username:

            messages.error(
                request,
                'El nombre de usuario es obligatorio.'
            )

            return redirect(
                'home:editar_usuario',
                pk=pk
            )

        if User.objects.filter(
            username=username
        ).exclude(pk=pk).exists():

            messages.error(
                request,
                'El nombre de usuario ya está registrado.'
            )

            return redirect(
                'home:editar_usuario',
                pk=pk
            )

        usuario.username = username
        usuario.email = email
        usuario.first_name = first_name

        usuario.last_name = (
            f'{apellido_paterno} {apellido_materno}'
        ).strip()

        if rol == 'administrador':

            usuario.is_staff = True
            usuario.is_superuser = True

        elif rol == 'editor':

            usuario.is_staff = True
            usuario.is_superuser = False

        else:

            usuario.is_staff = False
            usuario.is_superuser = False

        perfil.apellido_paterno = apellido_paterno
        perfil.apellido_materno = apellido_materno

        usuario.save()
        perfil.save()

        messages.success(
            request,
            'Usuario actualizado correctamente.'
        )

        return redirect('home:crud_usuarios')

    return render(
        request,
        'home/editar_usuario.html',
        {
            'usuario': usuario,
            'perfil': perfil,
        }
    )


# ==========================================
# BLOQUEAR USUARIO
# ==========================================

@operador_required
def bloquear_usuario(request, pk):

    if request.method != 'POST':
        return redirect('home:crud_usuarios')

    usuario = get_object_or_404(
        User,
        pk=pk
    )

    if usuario.pk == request.user.pk:

        messages.error(
            request,
            'No puedes bloquear tu propia cuenta.'
        )

    else:

        usuario.is_active = not usuario.is_active
        usuario.save()

        if usuario.is_active:

            messages.success(
                request,
                'Usuario activado correctamente.'
            )

        else:

            messages.success(
                request,
                'Usuario bloqueado correctamente.'
            )

    return redirect('home:crud_usuarios')


# ==========================================
# ELIMINAR USUARIO
# ==========================================

@operador_required
def eliminar_usuario(request, pk):

    if request.method != 'POST':
        return redirect('home:crud_usuarios')

    usuario = get_object_or_404(
        User,
        pk=pk
    )

    if usuario.pk == request.user.pk:

        messages.error(
            request,
            'No puedes eliminar tu propia cuenta.'
        )

    elif Comentario.objects.filter(
        user=usuario
    ).exists():

        messages.error(
            request,
            'No se puede eliminar este usuario porque tiene comentarios asociados. '
            'Puedes bloquear su cuenta para impedir que vuelva a iniciar sesión.'
        )

    else:

        try:

            with transaction.atomic():

                # Conserva archivos, categorías y publicaciones sin asignación.
                Archivo.objects.filter(
                    fk_user=usuario
                ).update(fk_user=None)

                Categoria.objects.filter(
                    fk_user=usuario
                ).update(fk_user=None)

                Publicacion.objects.filter(
                    autor=usuario
                ).update(autor=None)

                Perfil.objects.filter(
                    user=usuario
                ).delete()

                usuario.delete()

        except RestrictedError:

            messages.error(
                request,
                'No se puede eliminar este usuario porque aún tiene registros asociados. '
                'Bloquea la cuenta para conservar esos datos.'
            )

        else:

            messages.success(
                request,
                'Usuario eliminado. Sus publicaciones, categorías y archivos se conservaron sin asignación.'
            )

    return redirect('home:crud_usuarios')

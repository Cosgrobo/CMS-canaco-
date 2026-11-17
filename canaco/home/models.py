
from django.db import models
from django.contrib.auth.models import User


# ==========================================
# MODELO: CATEGORIA
# Tabla: categoria
# ==========================================

class Categoria(models.Model):

    id = models.BigAutoField(
        auto_created=True,
        primary_key=True,
        serialize=False,
        verbose_name='ID',
    )

    nombre = models.CharField(max_length=60)
    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(null=True, blank=True)

    fk_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        null=True,
        blank=True
    )

    class Meta:
        managed = True
        db_table = 'categoria'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


# ==========================================
# MODELO: ARCHIVO
# Tabla: archivo
# ==========================================

class Archivo(models.Model):

    id = models.BigAutoField(
        auto_created=True,
        primary_key=True,
        serialize=False,
        verbose_name='ID',
    )

    @property
    def display_url(self):
        if self.ruta:
            return self.ruta.url
        return ''

    nombre = models.CharField(max_length=255)
    nombre_temporal = models.CharField(max_length=255)
    ruta = models.FileField(upload_to='uploads/', max_length=100)
    tipo = models.CharField(max_length=100)
    tamano = models.PositiveIntegerField()

    createdat = models.DateTimeField(auto_now_add=True)

    fk_user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        null=True,
        blank=True
    )

    class Meta:
        managed = True
        db_table = 'archivo'
        verbose_name_plural = 'Archivos'

    def __str__(self):
        return self.nombre


# ==========================================
# MODELO: PERFIL
# Tabla: home_perfil
# ==========================================

class Perfil(models.Model):

    id = models.BigAutoField(
        auto_created=True,
        primary_key=True,
        serialize=False,
        verbose_name='ID',
    )

    apellido_paterno = models.CharField(max_length=80, blank=True)
    apellido_materno = models.CharField(max_length=80, blank=True)

    foto_perfil = models.ForeignKey(
        Archivo,
        on_delete=models.RESTRICT,
        null=True,
        blank=True
    )

    user = models.OneToOneField(
        User,
        on_delete=models.RESTRICT
    )

    class Meta:
        managed = True
        db_table = 'home_perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return f'Perfil de {self.user.username}'


# ==========================================
# MODELO: PUBLICACION
# Tabla: publicacion
# ==========================================

class Publicacion(models.Model):

    # Estados de las publicaciones
    ESTADO_BORRADOR = 'borrador'
    ESTADO_PUBLICADO = 'publicado'

    id = models.BigAutoField(
        auto_created=True,
        primary_key=True,
        serialize=False,
        verbose_name='ID',
    )

    titulo = models.CharField(max_length=180)
    resumen = models.TextField()
    contenido = models.TextField()

    estado = models.CharField(max_length=20)

    visitas = models.PositiveIntegerField()

    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)

    autor = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        null=True,
        blank=True
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.RESTRICT,
        null=True,
        blank=True
    )

    imagen_portada = models.ForeignKey(
        Archivo,
        on_delete=models.RESTRICT,
        null=True,
        blank=True
    )

    class Meta:
        managed = True
        db_table = 'publicacion'
        verbose_name_plural = 'Publicaciones'

    def __str__(self):
        return self.titulo


# ==========================================
# MODELO: GALERIA PUBLICACION
# Tabla: galeria_publicacion
# ==========================================

class GaleriaPublicacion(models.Model):

    id = models.BigAutoField(
        auto_created=True,
        primary_key=True,
        serialize=False,
        verbose_name='ID',
    )

    createdat = models.DateTimeField(auto_now_add=True)

    archivo = models.ForeignKey(
        Archivo,
        on_delete=models.RESTRICT
    )

    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.RESTRICT
    )

    class Meta:
        managed = True
        db_table = 'galeria_publicacion'
        verbose_name_plural = 'Galería de publicaciones'

    def __str__(self):
        return f'Galería de {self.publicacion.titulo}'


# ==========================================
# MODELO: COMENTARIO
# Tabla: comentario
# ==========================================

class Comentario(models.Model):

    # Estados de los comentarios
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADO = 'aprobado'
    ESTADO_BLOQUEADO = 'bloqueado'

    id = models.BigAutoField(
        auto_created=True,
        primary_key=True,
        serialize=False,
        verbose_name='ID',
    )

    contenido = models.TextField()
    estado = models.CharField(max_length=20)

    createdat = models.DateTimeField(auto_now_add=True)
    updatedat = models.DateTimeField(auto_now=True)

    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.RESTRICT
    )

    user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT
    )

    class Meta:
        managed = True
        db_table = 'comentario'
        verbose_name_plural = 'Comentarios'

    def __str__(self):
        return f'Comentario de {self.user.username}'

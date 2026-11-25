from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Categoria, Publicacion


class CategoriaAjaxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='category_admin',
            password='test-password',
            is_staff=True,
            is_superuser=True,
        )
        cls.editor = User.objects.create_user(
            username='category_editor',
            password='test-password',
            is_staff=False,
        )

    def setUp(self):
        self.client.force_login(self.admin)
        self.create_url = reverse('home:ajax_crear_categoria')

    def test_superadmin_can_create_and_empty_name_is_rejected(self):
        response = self.client.post(self.create_url, {'nombre': 'Comercio'})

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['categoria']['nombre'], 'Comercio')
        self.assertTrue(Categoria.objects.filter(nombre='Comercio').exists())

        response = self.client.post(self.create_url, {'nombre': '   '})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_duplicate_name_is_rejected(self):
        Categoria.objects.create(nombre='Comercio')

        response = self.client.post(self.create_url, {'nombre': ' comercio '})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(Categoria.objects.filter(nombre__iexact='comercio').count(), 1)

    def test_edit_updates_category_and_rejects_blank_name(self):
        category = Categoria.objects.create(nombre='Anterior')
        url = reverse('home:ajax_editar_categoria', args=[category.pk])

        response = self.client.post(url, {'nombre': 'Actualizada'})
        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.nombre, 'Actualizada')

        response = self.client.post(url, {'nombre': ''})
        self.assertEqual(response.status_code, 400)

    def test_delete_removes_unrelated_category(self):
        category = Categoria.objects.create(nombre='Temporal')
        url = reverse('home:ajax_eliminar_categoria', args=[category.pk])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Categoria.objects.filter(pk=category.pk).exists())

    def test_delete_respects_restricted_publication_relation(self):
        category = Categoria.objects.create(nombre='Con noticia')
        publication = Publicacion.objects.create(
            titulo='Noticia de prueba',
            resumen='',
            contenido='',
            estado=Publicacion.ESTADO_BORRADOR,
            visitas=0,
            categoria=category,
        )
        url = reverse('home:ajax_eliminar_categoria', args=[category.pk])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Categoria.objects.filter(pk=category.pk).exists())
        self.assertTrue(Publicacion.objects.filter(pk=publication.pk).exists())

    def test_non_staff_user_cannot_manage_categories(self):
        self.client.force_login(self.editor)

        response = self.client.post(self.create_url, {'nombre': 'Bloqueada'})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Categoria.objects.filter(nombre='Bloqueada').exists())

    def test_anonymous_user_cannot_manage_categories(self):
        self.client.logout()

        response = self.client.post(self.create_url, {'nombre': 'Bloqueada'})

        self.assertEqual(response.status_code, 401)

    def test_csrf_token_is_required(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)

        response = csrf_client.post(self.create_url, {'nombre': 'Sin token'})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Categoria.objects.filter(nombre='Sin token').exists())

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import tempfile
import shutil

from posts.forms import PostForm
from posts.models import Group, Post, User


class TestCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.group = Group.objects.create(
            title='Лев Толстой',
            slug='tolstoy',
            description='Группа Льва Толстого',
        )

        cls.group_change = Group.objects.create(
            title="тест",
            slug='test_group',
            description='тест замена'
        )

        cls.author = User.objects.create_user(
            username='authorForPosts',
            first_name='Тестов',
            last_name='Теcтовский',
            email='testuser@yatube.ru'
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            group=TestCreateForm.group,
            text="Какой-то там текст",
            author=User.objects.get(username='authorForPosts'),
            image=uploaded
        )

        cls.form = PostForm()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='TestForTest')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_form_create(self):
        """Проверка создания нового поста, авторизированным пользователем"""
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Отправить текст',
            'image': self.post.image.name
        }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response, reverse('posts:profile',
                                               args=[self.user]))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Отправить текст',
            group=TestCreateForm.group).exists())

    def test_form_edit(self):
        """
        Проверка редактирования поста через форму на странице
        """
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        url = reverse('posts:post_edit', args=[1])
        self.authorized_client.get(url)
        form_data = {
            'group': self.group_change.id,
            'text': 'Обновленный текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[1]),
            data=form_data, follow=True)

        self.assertTrue(Post.objects.filter(
            text='Обновленный текст',
            group=self.group_change).exists())
        self.assertEqual(self.group.id, TestCreateForm.group.id)

    def test_form_create_anonym(self):
        """Проверка создания нового поста, анонимным пользователем"""
        self.guest_client = Client()
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Отправить текст',
        }
        response = self.guest_client.post(reverse('posts:post_create'),
                                          data=form_data,
                                          follow=True)
        self.assertRedirects(response,
                             f"{reverse('users:login')}?next=/create/")
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(Post.objects.filter(
            text='Отправить текст',
            group=TestCreateForm.group).exists())

    def test_form_edit_anonym(self):
        """
        Проверка редактирования поста анонимусом через форму на странице
        """
        url = reverse('posts:post_edit', args=[1])
        self.guest_client.get(url)
        form_data = {
            'group': self.group.id,
            'text': 'Обновленный текст',
        }
        self.guest_client.post(
            reverse('posts:post_edit', args=[1]),
            data=form_data, follow=True)

        self.assertFalse(Post.objects.filter(
            text='Обновленный текст',
            group=TestCreateForm.group).exists())

    def test_form_edit_auth_not_author(self):
        """
        Проверка редактирования поста не автором через форму на странице
        """
        self.user = User.objects.create_user(username='Hacker')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        url = reverse('posts:post_edit', args=[1])
        self.authorized_client.get(url)
        form_data = {
            'group': self.group.id,
            'text': 'Обновленный текст',
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[1]),
            data=form_data, follow=True)

        self.assertFalse(Post.objects.filter(
            text='Обновленный текст',
            group=TestCreateForm.group).exists())

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
import datetime
import uuid

from catalog.models import Author, Book, BookInstance, Genre


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create 13 authors for pagination tests
        number_of_authors = 13
        for author_num in range(number_of_authors):
            Author.objects.create(
                first_name='Christian %s' % author_num,
                last_name='Surname %s' % author_num,
            )

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/catalog/authors/')
        self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        resp = self.client.get(reverse('authors'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertTrue(len(resp.context['author_list']) == 10)

    def test_lists_all_authors(self):
        # Get second page and confirm it has (exactly) remaining 3 items
        resp = self.client.get(reverse('authors') + '?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertTrue(len(resp.context['author_list']) == 3)


class RenewBookInstancesViewTest(TestCase):

    def setUp(self):
        # Создание пользователя
        test_user1 = User.objects.create_user(username='testuser1', password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(username='testuser2', password='12345')
        test_user2.save()

        # Присваивание разрешения 'Set book as returned'
        permission = Permission.objects.get(codename='can_mark_returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        # Создание книги (БЕЗ Language)
        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_book = Book.objects.create(
            title='Book Title',
            summary='My book summary',
            isbn='ABCDEFG',
            author=test_author,
        )
        # Создание жанра
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # Создание объекта BookInstance для пользователя test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user1,
            status='o'
        )

        # Создание объекта BookInstance для пользователя test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(
            book=test_book,
            imprint='Unlikely Imprint, 2016',
            due_back=return_date,
            borrower=test_user2,
            status='o'
        )

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_redirect_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_logged_in_with_permission_borrowed_book(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance2.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        test_uid = uuid.uuid4()  # unlikely UID to match our bookinstance!
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': test_uid}))
        self.assertEqual(resp.status_code, 404)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/book_renew_librarian.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)
        date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(resp.context['form'].initial['renewal_date'], date_3_weeks_in_future)

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(username='testuser2', password='12345')
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        resp = self.client.post(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': valid_date_in_future}
        )
        self.assertRedirects(resp, reverse('all-borrowed'))

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(username='testuser2', password='12345')
        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
        resp = self.client.post(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': date_in_past}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context['form'], 'renewal_date', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(username='testuser2', password='12345')
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
        resp = self.client.post(
            reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk}),
            {'renewal_date': invalid_date_in_future}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp.context['form'], 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')


class AuthorCreateViewTest(TestCase):

    def setUp(self):
        # Создание пользователей
        self.test_user1 = User.objects.create_user(username='testuser1', password='12345')
        self.test_user1.save()

        self.test_user2 = User.objects.create_user(username='testuser2', password='12345')
        self.test_user2.save()

    def test_access_without_login(self):
        """Проверка доступа для неавторизованного пользователя"""
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)  # Должен быть доступен без логина

    def test_access_with_login(self):
        """Проверка доступа для авторизованного пользователя"""
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)  # Должен быть доступен с логином

    def test_uses_correct_template(self):
        """Проверка использования правильного шаблона"""
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/author_form.html')

    def test_initial_date_of_death(self):
        """Проверка начального значения даты смерти"""
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)

        # Проверяем начальное значение даты смерти
        expected_date = '12/10/2016'
        self.assertEqual(resp.context['form'].initial['date_of_death'], expected_date)

    def test_form_fields(self):
        """Проверка полей формы"""
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)

        # Проверяем, что форма содержит все необходимые поля
        form = resp.context['form']
        expected_fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_redirects_to_author_detail_on_success(self):
        """Проверка редиректа после успешного создания автора"""
        # Данные для создания автора
        author_data = {
            'first_name': 'Test',
            'last_name': 'Author',
            'date_of_birth': '1980-01-01',
            'date_of_death': '2020-01-01'
        }

        resp = self.client.post(reverse('author-create'), author_data)

        # После успешного создания должен быть редирект на страницу автора
        self.assertEqual(resp.status_code, 302)

        # Получаем созданного автора
        author = Author.objects.get(first_name='Test', last_name='Author')
        expected_url = reverse('author-detail', kwargs={'pk': author.pk})
        self.assertRedirects(resp, expected_url)

    def test_author_creation(self):
        """Проверка фактического создания автора в базе данных"""
        initial_count = Author.objects.count()

        author_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1975-05-15',
            'date_of_death': '2020-12-31'
        }

        resp = self.client.post(reverse('author-create'), author_data)

        # Проверяем, что автор был создан
        self.assertEqual(Author.objects.count(), initial_count + 1)

        # Проверяем данные созданного автора
        new_author = Author.objects.get(first_name='John', last_name='Doe')
        self.assertEqual(str(new_author.date_of_birth), '1975-05-15')
        self.assertEqual(str(new_author.date_of_death), '2020-12-31')

    def test_invalid_form_submission(self):
        """Проверка обработки невалидной формы"""
        # Отправляем форму с неполными данными
        invalid_data = {
            'first_name': '',  # Обязательное поле пустое
            'last_name': 'Test',
        }

        resp = self.client.post(reverse('author-create'), invalid_data)

        # Должна вернуться форма с ошибками
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['form'].errors)
        self.assertIn('first_name', resp.context['form'].errors)
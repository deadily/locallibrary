from django.test import TestCase
from catalog.models import Author, Book, Genre, BookInstance  # Добавьте этот импорт

class AuthorModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        Author.objects.create(first_name='John', last_name='Doe')

    def test_first_name_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('first_name').verbose_name
        self.assertEqual(field_label, 'first name')

    def test_first_name_max_length(self):
        author = Author.objects.get(id=1)
        max_length = author._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 100)

    def test_object_name_is_last_name_comma_first_name(self):
        author = Author.objects.get(id=1)
        expected_object_name = f'{author.last_name}, {author.first_name}'
        self.assertEqual(str(author), expected_object_name)

    def test_get_absolute_url(self):
        author = Author.objects.get(id=1)
        self.assertEqual(author.get_absolute_url(), '/catalog/author/1')

class BookModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create an author for the book
        author = Author.objects.create(first_name='John', last_name='Doe')
        # Create a book
        Book.objects.create(
            title='Test Book',
            author=author,
            summary='Test summary',
            isbn='1234567890123'
        )

    def test_book_str(self):
        book = Book.objects.get(id=1)
        self.assertEqual(str(book), 'Test Book')

    def test_get_absolute_url(self):
        book = Book.objects.get(id=1)
        self.assertEqual(book.get_absolute_url(), '/catalog/book/1')
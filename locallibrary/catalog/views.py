from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db.models import Q  # Добавляем импорт Q
from django.views import generic
from .models import Book, Author, BookInstance, Genre

def index(request):
    # Генерация "количеств" некоторых главных объектов
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Доступные книги (статус = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()
    num_genres = Genre.objects.count()  # Добавляем количество жанров

    # Поиск книг по ключевым словам (ПЕРЕД return)
    search_words = ["война", "мир", "любовь", "death", "time", "science", "fantasy"]
    books_with_words = {}

    for word in search_words:
        count = Book.objects.filter(Q(title__icontains=word)).count()
        if count > 0:
            books_with_words[word] = count

    # Сортируем словарь по значениям (количеству книг) в убывающем порядке
    sorted_books_with_words = dict(sorted(
        books_with_words.items(),
        key=lambda item: item[1],
        reverse=True
    ))

    # Счетчик посещений
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    return render(
        request,
        'index.html',
        context={
            'num_books': num_books,
            'num_instances': num_instances,
            'num_instances_available': num_instances_available,
            'num_authors': num_authors,
            'num_genres': num_genres,  # Добавляем количество жанров
            'num_visits': num_visits,
            'books_with_words': sorted_books_with_words,  # Добавляем отсортированный словарь
        },
    )

class BookListView(generic.ListView):
    model = Book
    paginate_by = 2

class BookDetailView(generic.DetailView):
    model = Book

    def book_detail_view(request, pk):
        try:
            book_id = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            raise Http404("Book does not exist")

        return render(
            request,
            'catalog/book_detail.html',
            context={'book': book_id, }
        )


class AuthorDetailView(generic.DetailView):
    model = Author
    paginate_by = 2


class AuthorListView(generic.ListView):
    model = Author

    def author_detail_view(request, pk):
        try:
            author_id = Author.objects.get(pk=pk)
        except Author.DoesNotExist:
            raise Http404("Author does not exist")

        return render(
            request,
            'catalog/author_detail.html',
            context={'author': author_id, }
        )
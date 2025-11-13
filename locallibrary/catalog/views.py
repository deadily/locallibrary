from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.db.models import Q  # Добавляем импорт Q
from django.views import generic
from django.views.generic import CreateView, UpdateView, DeleteView

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
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book



class AuthorDetailView(generic.DetailView):
    model = Author
    paginate_by = 10


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


from django.contrib.auth.decorators import permission_required

from django.urls import reverse, reverse_lazy
import datetime

from .forms import RenewBookForm

@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})


from django.contrib.auth.mixins import PermissionRequiredMixin


class AllBorrowedBooksListView(PermissionRequiredMixin, generic.ListView):
    """
    Представление для отображения всех взятых книг, доступно только библиотекарям
    с разрешением can_mark_returned
    """
    model = BookInstance
    template_name = 'catalog/all_borrowed_books.html'
    context_object_name = 'borrowed_books'
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        """Возвращаем только взятые книги (статус 'o' - on loan)"""
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial={'date_of_death':'12/10/2016',}

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
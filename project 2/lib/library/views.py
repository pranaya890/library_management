from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import Book, Author, Publisher, Member, Transaction
from .forms import BookForm, MemberForm  # You'll need to create these forms
from datetime import timedelta
from django.utils import timezone

def home(request):
    """
    Home page view with basic statistics
    """
    context = {
        'total_books': Book.objects.count(),
        'total_members': Member.objects.count(),
        'books_issued': Transaction.objects.filter(return_date__isnull=True).count(),
        'overdue_books': Transaction.objects.filter(
            return_date__isnull=True,
            due_date__lt=timezone.now().date()
        ).count(),
    }
    return render(request, 'library/home.html', context)

def book_list(request):
    """
    Display list of all books with search and filter functionality
    """
    books = Book.objects.all().select_related('author', 'publisher')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__name__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(publisher__name__icontains=search_query)
        )
    
    # Filter by availability
    availability = request.GET.get('availability')
    if availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability == 'unavailable':
        books = books.filter(available_copies=0)
    
    # Filter by category/genre
    category = request.GET.get('category')
    if category:
        books = books.filter(category=category)
    
    # Get unique categories for filter dropdown
    categories = Book.objects.values_list('category', flat=True).distinct()
    
    context = {
        'books': books,
        'search_query': search_query,
        'categories': categories,
        'selected_category': category,
        'selected_availability': availability,
    }
    
    return render(request, 'library/book_list.html', context)

def book_detail(request, pk):
    """
    Display detailed information about a specific book
    """
    book = get_object_or_404(Book, pk=pk)
    
    # Get transaction history for this book
    transactions = Transaction.objects.filter(book=book).select_related('member').order_by('-issue_date')
    
    context = {
        'book': book,
        'transactions': transactions,
        'is_available': book.available_copies > 0,
    }
    
    return render(request, 'library/book_detail.html', context)

@login_required
def add_book(request):
    """
    Add a new book to the library
    """
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" has been added successfully!')
            return redirect('library:book_detail', pk=book.pk)
    else:
        form = BookForm()
    
    context = {
        'form': form,
        'title': 'Add New Book'
    }
    
    return render(request, 'library/book_form.html', context)

def member_list(request):
    """
    Display list of all library members
    """
    members = Member.objects.all().annotate(
        books_borrowed=Count('transaction', filter=Q(transaction__return_date__isnull=True))
    )
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        members = members.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(member_id__icontains=search_query)
        )
    
    context = {
        'members': members,
        'search_query': search_query,
    }
    
    return render(request, 'library/member_list.html', context)

def transaction_list(request):
    """
    Display list of all transactions (issued and returned books)
    """
    transactions = Transaction.objects.all().select_related('book', 'member').order_by('-issue_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'issued':
        transactions = transactions.filter(return_date__isnull=True)
    elif status == 'returned':
        transactions = transactions.filter(return_date__isnull=False)
    elif status == 'overdue':
        from django.utils import timezone
        transactions = transactions.filter(
            return_date__isnull=True,
            due_date__lt=timezone.now().date()
        )
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        transactions = transactions.filter(
            Q(book__title__icontains=search_query) |
            Q(member__name__icontains=search_query) |
            Q(member__member_id__icontains=search_query)
        )
    
    context = {
        'transactions': transactions,
        'search_query': search_query,
        'selected_status': status,
    }
    
    return render(request, 'library/transaction_list.html', context)

def reports(request):
    """
    Generate various reports and statistics
    """
    from django.utils import timezone
    from django.db.models import Sum, Avg
    from datetime import timedelta
    
    # Basic statistics
    total_books = Book.objects.count()
    total_members = Member.objects.count()
    total_transactions = Transaction.objects.count()
    books_issued = Transaction.objects.filter(return_date__isnull=True).count()
    
    # Overdue books
    overdue_books = Transaction.objects.filter(
        return_date__isnull=True,
        due_date__lt=timezone.now().date()
    ).count()
    
    # Most popular books (by number of times borrowed)
    popular_books = Book.objects.annotate(
        borrow_count=Count('transaction')
    ).order_by('-borrow_count')[:10]
    
    # Most active members
    active_members = Member.objects.annotate(
        borrow_count=Count('transaction')
    ).order_by('-borrow_count')[:10]
    
    # Monthly statistics for the last 6 months
    monthly_stats = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_transactions = Transaction.objects.filter(
            issue_date__range=[month_start, month_end]
        ).count()
        monthly_stats.append({
            'month': month_start.strftime('%B %Y'),
            'transactions': month_transactions
        })
    
    context = {
        'total_books': total_books,
        'total_members': total_members,
        'total_transactions': total_transactions,
        'books_issued': books_issued,
        'overdue_books': overdue_books,
        'popular_books': popular_books,
        'active_members': active_members,
        'monthly_stats': monthly_stats,
    }
    
    return render(request, 'library/reports.html', context)

def login_view(request):
    """
    User login view
    """
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'You have been logged in successfully!')
            return redirect('library:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'library/login.html')

def signup_view(request):
    """
    User registration view
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('library:login')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'library/signup.html', context)

def logout_view(request):
    """
    User logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('library:home')

# Additional utility views

@login_required
def issue_book(request, book_id):
    """
    Issue a book to a member
    """
    book = get_object_or_404(Book, pk=book_id)
    
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        member = get_object_or_404(Member, member_id=member_id)
        
        if book.available_copies > 0:
            # Create transaction
            transaction = Transaction.objects.create(
                book=book,
                member=member,
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=14)  # 2 weeks
            )
            
            # Update book available copies
            book.available_copies -= 1
            book.save()
            
            messages.success(request, f'Book "{book.title}" issued to {member.name}')
            return redirect('library:book_detail', pk=book.pk)
        else:
            messages.error(request, 'Book is not available')
    
    context = {
        'book': book,
        'members': Member.objects.all()
    }
    
    return render(request, 'library/issue_book.html', context)

@login_required
def return_book(request, transaction_id):
    """
    Return a book
    """
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    if request.method == 'POST':
        # Mark as returned
        transaction.return_date = timezone.now().date()
        transaction.save()
        
        # Update book available copies
        book = transaction.book
        book.available_copies += 1
        book.save()
        
        messages.success(request, f'Book "{book.title}" returned successfully')
        return redirect('library:transaction_list')
    
    context = {
        'transaction': transaction
    }
    
    return render(request, 'library/return_book.html', context)

# AJAX views for dynamic functionality
def search_books_ajax(request):
    """
    AJAX endpoint for book search
    """
    query = request.GET.get('q', '')
    books = Book.objects.filter(
        Q(title__icontains=query) |
        Q(author__name__icontains=query) |
        Q(isbn__icontains=query)
    )[:10]  # Limit to 10 results
    
    results = []
    for book in books:
        results.append({
            'id': book.id,
            'title': book.title,
            'author': book.author.name if book.author else '',
            'isbn': book.isbn,
            'available': book.available_copies > 0
        })
    
    return JsonResponse({'results': results})
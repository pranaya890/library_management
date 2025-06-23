# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib import messages
# from django.http import JsonResponse
# from django.db.models import Q, Count
# from .models import Book, Author, Publisher, Member, Transaction
# from .forms import BookForm, MemberForm  # You'll need to create these forms
# from datetime import timedelta
# from django.utils import timezone

# def home(request):
#     """
#     Home page view with basic statistics
#     """
#     context = {
#         'total_books': Book.objects.count(),
#         'total_members': Member.objects.count(),
#         'books_issued': Transaction.objects.filter(return_date__isnull=True).count(),
#         'overdue_books': Transaction.objects.filter(
#             return_date__isnull=True,
#             due_date__lt=timezone.now().date()
#         ).count(),
#     }
#     return render(request, 'library/home.html', context)

# def book_list(request):
#     """
#     Display list of all books with search and filter functionality
#     """
#     books = Book.objects.all().select_related('author', 'publisher')
    
#     # Search functionality
#     search_query = request.GET.get('search')
#     if search_query:
#         books = books.filter(
#             Q(title__icontains=search_query) |
#             Q(author__name__icontains=search_query) |
#             Q(isbn__icontains=search_query) |
#             Q(publisher__name__icontains=search_query)
#         )
    
#     # Filter by availability
#     availability = request.GET.get('availability')
#     if availability == 'available':
#         books = books.filter(available_copies__gt=0)
#     elif availability == 'unavailable':
#         books = books.filter(available_copies=0)
    
#     # Filter by category/genre
#     category = request.GET.get('category')
#     if category:
#         books = books.filter(category=category)
    
#     # Get unique categories for filter dropdown
#     categories = Book.objects.values_list('category', flat=True).distinct()
    
#     context = {
#         'books': books,
#         'search_query': search_query,
#         'categories': categories,
#         'selected_category': category,
#         'selected_availability': availability,
#     }
    
#     return render(request, 'library/book_list.html', context)

# def book_detail(request, pk):
#     """
#     Display detailed information about a specific book
#     """
#     book = get_object_or_404(Book, pk=pk)
    
#     # Get transaction history for this book
#     transactions = Transaction.objects.filter(book=book).select_related('member').order_by('-issue_date')
    
#     context = {
#         'book': book,
#         'transactions': transactions,
#         'is_available': book.available_copies > 0,
#     }
    
#     return render(request, 'library/book_detail.html', context)

# @login_required
# def add_book(request):
#     """
#     Add a new book to the library
#     """
#     if request.method == 'POST':
#         form = BookForm(request.POST, request.FILES)
#         if form.is_valid():
#             book = form.save()
#             messages.success(request, f'Book "{book.title}" has been added successfully!')
#             return redirect('library:book_detail', pk=book.pk)
#     else:
#         form = BookForm()
    
#     context = {
#         'form': form,
#         'title': 'Add New Book'
#     }
    
#     return render(request, 'library/book_form.html', context)

# def member_list(request):
#     """
#     Display list of all library members
#     """
#     members = Member.objects.all().annotate(
#         books_borrowed=Count('transaction', filter=Q(transaction__return_date__isnull=True))
#     )
    
#     # Search functionality
#     search_query = request.GET.get('search')
#     if search_query:
#         members = members.filter(
#             Q(name__icontains=search_query) |
#             Q(email__icontains=search_query) |
#             Q(phone__icontains=search_query) |
#             Q(member_id__icontains=search_query)
#         )
    
#     context = {
#         'members': members,
#         'search_query': search_query,
#     }
    
#     return render(request, 'library/member_list.html', context)

# def transaction_list(request):
#     """
#     Display list of all transactions (issued and returned books)
#     """
#     transactions = Transaction.objects.all().select_related('book', 'member').order_by('-issue_date')
    
#     # Filter by status
#     status = request.GET.get('status')
#     if status == 'issued':
#         transactions = transactions.filter(return_date__isnull=True)
#     elif status == 'returned':
#         transactions = transactions.filter(return_date__isnull=False)
#     elif status == 'overdue':
#         from django.utils import timezone
#         transactions = transactions.filter(
#             return_date__isnull=True,
#             due_date__lt=timezone.now().date()
#         )
    
#     # Search functionality
#     search_query = request.GET.get('search')
#     if search_query:
#         transactions = transactions.filter(
#             Q(book__title__icontains=search_query) |
#             Q(member__name__icontains=search_query) |
#             Q(member__member_id__icontains=search_query)
#         )
    
#     context = {
#         'transactions': transactions,
#         'search_query': search_query,
#         'selected_status': status,
#     }
    
#     return render(request, 'library/transaction_list.html', context)

# def reports(request):
#     """
#     Generate various reports and statistics
#     """
#     from django.utils import timezone
#     from django.db.models import Sum, Avg
#     from datetime import timedelta
    
#     # Basic statistics
#     total_books = Book.objects.count()
#     total_members = Member.objects.count()
#     total_transactions = Transaction.objects.count()
#     books_issued = Transaction.objects.filter(return_date__isnull=True).count()
    
#     # Overdue books
#     overdue_books = Transaction.objects.filter(
#         return_date__isnull=True,
#         due_date__lt=timezone.now().date()
#     ).count()
    
#     # Most popular books (by number of times borrowed)
#     popular_books = Book.objects.annotate(
#         borrow_count=Count('transaction')
#     ).order_by('-borrow_count')[:10]
    
#     # Most active members
#     active_members = Member.objects.annotate(
#         borrow_count=Count('transaction')
#     ).order_by('-borrow_count')[:10]
    
#     # Monthly statistics for the last 6 months
#     monthly_stats = []
#     for i in range(6):
#         month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
#         month_end = month_start.replace(day=28) + timedelta(days=4)
#         month_transactions = Transaction.objects.filter(
#             issue_date__range=[month_start, month_end]
#         ).count()
#         monthly_stats.append({
#             'month': month_start.strftime('%B %Y'),
#             'transactions': month_transactions
#         })
    
#     context = {
#         'total_books': total_books,
#         'total_members': total_members,
#         'total_transactions': total_transactions,
#         'books_issued': books_issued,
#         'overdue_books': overdue_books,
#         'popular_books': popular_books,
#         'active_members': active_members,
#         'monthly_stats': monthly_stats,
#     }
    
#     return render(request, 'library/reports.html', context)

# def login_view(request):
#     """
#     User login view
#     """
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
        
#         if user is not None:
#             login(request, user)
#             messages.success(request, 'You have been logged in successfully!')
#             return redirect('library:home')
#         else:
#             messages.error(request, 'Invalid username or password.')
    
#     return render(request, 'library/login.html')

# def signup_view(request):
#     """
#     User registration view
#     """
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             username = form.cleaned_data.get('username')
#             messages.success(request, f'Account created for {username}! You can now log in.')
#             return redirect('library:login')
#     else:
#         form = UserCreationForm()
    
#     context = {
#         'form': form
#     }
    
#     return render(request, 'library/signup.html', context)

# def logout_view(request):
#     """
#     User logout view
#     """
#     logout(request)
#     messages.success(request, 'You have been logged out successfully!')
#     return redirect('library:home')

# # Additional utility views

# @login_required
# def issue_book(request, book_id):
#     """
#     Issue a book to a member
#     """
#     book = get_object_or_404(Book, pk=book_id)
    
#     if request.method == 'POST':
#         member_id = request.POST.get('member_id')
#         member = get_object_or_404(Member, member_id=member_id)
        
#         if book.available_copies > 0:
#             # Create transaction
#             transaction = Transaction.objects.create(
#                 book=book,
#                 member=member,
#                 issue_date=timezone.now().date(),
#                 due_date=timezone.now().date() + timedelta(days=14)  # 2 weeks
#             )
            
#             # Update book available copies
#             book.available_copies -= 1
#             book.save()
            
#             messages.success(request, f'Book "{book.title}" issued to {member.name}')
#             return redirect('library:book_detail', pk=book.pk)
#         else:
#             messages.error(request, 'Book is not available')
    
#     context = {
#         'book': book,
#         'members': Member.objects.all()
#     }
    
#     return render(request, 'library/issue_book.html', context)

# @login_required
# def return_book(request, transaction_id):
#     """
#     Return a book
#     """
#     transaction = get_object_or_404(Transaction, pk=transaction_id)
    
#     if request.method == 'POST':
#         # Mark as returned
#         transaction.return_date = timezone.now().date()
#         transaction.save()
        
#         # Update book available copies
#         book = transaction.book
#         book.available_copies += 1
#         book.save()
        
#         messages.success(request, f'Book "{book.title}" returned successfully')
#         return redirect('library:transaction_list')
    
#     context = {
#         'transaction': transaction
#     }
    
#     return render(request, 'library/return_book.html', context)

# # AJAX views for dynamic functionality
# def search_books_ajax(request):
#     """
#     AJAX endpoint for book search
#     """
#     query = request.GET.get('q', '')
#     books = Book.objects.filter(
#         Q(title__icontains=query) |
#         Q(author__name__icontains=query) |
#         Q(isbn__icontains=query)
#     )[:10]  # Limit to 10 results
    
#     results = []
#     for book in books:
#         results.append({
#             'id': book.id,
#             'title': book.title,
#             'author': book.author.name if book.author else '',
#             'isbn': book.isbn,
#             'available': book.available_copies > 0
#         })
    
#     return JsonResponse({'results': results})


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
    # FIX 1: Change select_related('author') to prefetch_related('authors')
    books = Book.objects.all().select_related('publisher', 'category').prefetch_related('authors')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        # FIX 2: Change author__name to authors__name for ManyToMany field
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(authors__name__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(publisher__name__icontains=search_query)
        ).distinct()  # Add distinct() to avoid duplicates from ManyToMany joins
    
    # Filter by availability
    availability = request.GET.get('availability')
    if availability == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability == 'unavailable':
        books = books.filter(available_copies=0)
    
    # Filter by category/genre
    category = request.GET.get('category')
    if category:
        books = books.filter(category__name=category)  # Assuming category is a ForeignKey
    
    # Get unique categories for filter dropdown
    # FIX 3: Get category names properly
    categories = Book.objects.select_related('category').exclude(category__isnull=True).values_list('category__name', flat=True).distinct()
    
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

@login_required
def add_member(request):
    """
    Add a new member to the library
    """
    if request.method == 'POST':
        form = MemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save()
            messages.success(request, f'Member "{member.name}" has been added successfully!')
            return redirect('library:member_detail', pk=member.pk)
    else:
        form = MemberForm()
    
    context = {
        'form': form,
        'title': 'Add New Member'
    }
    
    return render(request, 'library/member_form.html', context)

def member_list(request):
    """
    Display list of all library members
    """
    # Get all members with related user data
    members = Member.objects.select_related('user').all()
    
    # Calculate statistics
    total_members = members.count()
    active_members = members.filter(status='ACTIVE').count()
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        members = members.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(member_id__icontains=search_query)
        )
    
    context = {
        'members': members,
        'search_query': search_query,
        'total_members': total_members,
        'active_members': active_members,
    }
    
    return render(request, 'library/member_list.html', context)


def member_detail(request, pk):
    """
    Display detailed information about a specific member
    """
    member = get_object_or_404(Member, pk=pk)
    
    # Get current borrowed books
    current_books = Transaction.objects.filter(
        member=member, 
        return_date__isnull=True
    ).select_related('book')
    
    # Get transaction history
    transaction_history = Transaction.objects.filter(
        member=member
    ).select_related('book').order_by('-issue_date')
    
    # Check for overdue books
    overdue_books = Transaction.objects.filter(
        member=member,
        return_date__isnull=True,
        due_date__lt=timezone.now().date()
    ).select_related('book')
    
    context = {
        'member': member,
        'current_books': current_books,
        'transaction_history': transaction_history,
        'overdue_books': overdue_books,
        'total_borrowed': transaction_history.count(),
        'currently_borrowed': current_books.count(),
    }
    
    return render(request, 'library/member_detail.html', context)

@login_required
def checkout_book(request):
    """
    Checkout/Issue a book to a member
    """
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        member_id = request.POST.get('member_id')
        
        book = get_object_or_404(Book, pk=book_id)
        member = get_object_or_404(Member, pk=member_id)
        
        # Check if book is available
        if book.available_copies <= 0:
            messages.error(request, f'Book "{book.title}" is not available for checkout.')
            return redirect('library:checkout_book')
        
        # Check if member already has this book
        existing_transaction = Transaction.objects.filter(
            book=book,
            member=member,
            return_date__isnull=True
        ).exists()
        
        if existing_transaction:
            messages.error(request, f'Member "{member.name}" already has this book checked out.')
            return redirect('library:checkout_book')
        
        # Check member's borrowing limit (assuming max 5 books)
        current_borrowed = Transaction.objects.filter(
            member=member,
            return_date__isnull=True
        ).count()
        
        if current_borrowed >= 5:
            messages.error(request, f'Member "{member.name}" has reached the maximum borrowing limit.')
            return redirect('library:checkout_book')
        
        # Create transaction
        due_date = timezone.now().date() + timedelta(days=14)  # 2 weeks loan period
        transaction = Transaction.objects.create(
            book=book,
            member=member,
            issue_date=timezone.now().date(),
            due_date=due_date
        )
        
        # Update book available copies
        book.available_copies -= 1
        book.save()
        
        messages.success(request, f'Book "{book.title}" successfully checked out to {member.name}. Due date: {due_date}')
        return redirect('library:transaction_detail', pk=transaction.pk)
    
    # GET request - show checkout form
    books = Book.objects.filter(available_copies__gt=0).select_related('author')
    members = Member.objects.all().order_by('name')
    
    context = {
        'books': books,
        'members': members,
        'title': 'Checkout Book'
    }
    
    return render(request, 'library/checkout_book.html', context)

@login_required
def return_book(request, transaction_id=None):
    """
    Return a book
    """
    transaction = None
    if transaction_id:
        transaction = get_object_or_404(Transaction, pk=transaction_id, return_date__isnull=True)
    
    if request.method == 'POST':
        if not transaction_id:
            # If no transaction_id in URL, get it from form
            transaction_id = request.POST.get('transaction_id')
            transaction = get_object_or_404(Transaction, pk=transaction_id, return_date__isnull=True)
        
        # Calculate fine if overdue
        fine_amount = 0
        return_date = timezone.now().date()
        if return_date > transaction.due_date:
            overdue_days = (return_date - transaction.due_date).days
            fine_amount = overdue_days * 1.00  # $1 per day fine
        
        # Mark as returned
        transaction.return_date = return_date
        transaction.fine_amount = fine_amount
        transaction.save()
        
        # Update book available copies
        book = transaction.book
        book.available_copies += 1
        book.save()
        
        if fine_amount > 0:
            messages.warning(request, f'Book "{book.title}" returned successfully. Late fee: ${fine_amount:.2f}')
        else:
            messages.success(request, f'Book "{book.title}" returned successfully.')
        
        return redirect('library:transaction_list')
    
    # GET request
    if transaction:
        context = {
            'transaction': transaction,
            'title': 'Return Book'
        }
    else:
        # Show all issued books for selection
        issued_transactions = Transaction.objects.filter(
            return_date__isnull=True
        ).select_related('book', 'member').order_by('due_date')
        
        context = {
            'issued_transactions': issued_transactions,
            'title': 'Return Book'
        }
    
    return render(request, 'library/return_book.html', context)

def overdue_books(request):
    """
    Display all overdue books
    """
    overdue_transactions = Transaction.objects.filter(
        return_date__isnull=True,
        due_date__lt=timezone.now().date()
    ).select_related('book', 'member').order_by('due_date')
    
    # Calculate fine for each overdue book
    for transaction in overdue_transactions:
        overdue_days = (timezone.now().date() - transaction.due_date).days
        transaction.calculated_fine = overdue_days * 1.00  # $1 per day
        transaction.overdue_days = overdue_days
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        overdue_transactions = overdue_transactions.filter(
            Q(book__title__icontains=search_query) |
            Q(member__name__icontains=search_query) |
            Q(member__member_id__icontains=search_query)
        )
    
    # Calculate total fine amount
    total_fine = sum(transaction.calculated_fine for transaction in overdue_transactions)
    
    context = {
        'overdue_transactions': overdue_transactions,
        'total_overdue': overdue_transactions.count(),
        'total_fine': total_fine,
        'search_query': search_query,
        'title': 'Overdue Books'
    }
    
    return render(request, 'library/overdue_books.html', context)

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

def transaction_detail(request, pk):
    """
    Display detailed information about a specific transaction
    """
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Calculate fine if overdue and not returned
    fine_amount = 0
    overdue_days = 0
    if not transaction.return_date and timezone.now().date() > transaction.due_date:
        overdue_days = (timezone.now().date() - transaction.due_date).days
        fine_amount = overdue_days * 1.00  # $1 per day
    elif transaction.return_date and transaction.return_date > transaction.due_date:
        overdue_days = (transaction.return_date - transaction.due_date).days
        fine_amount = transaction.fine_amount or (overdue_days * 1.00)
    
    context = {
        'transaction': transaction,
        'fine_amount': fine_amount,
        'overdue_days': overdue_days,
        'is_overdue': overdue_days > 0,
        'is_returned': transaction.return_date is not None,
    }
    
    return render(request, 'library/transaction_detail.html', context)

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

def get_available_books_ajax(request):
    """
    AJAX endpoint to get available books for checkout
    """
    query = request.GET.get('q', '')
    books = Book.objects.filter(
        available_copies__gt=0
    ).select_related('author')
    
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(isbn__icontains=query)
        )
    
    books = books[:10]  # Limit to 10 results
    
    results = []
    for book in books:
        results.append({
            'id': book.id,
            'title': book.title,
            'author': book.author.name if book.author else 'Unknown',
            'isbn': book.isbn,
            'available_copies': book.available_copies
        })
    
    return JsonResponse({'results': results})

def get_members_ajax(request):
    """
    AJAX endpoint to search members
    """
    query = request.GET.get('q', '')
    members = Member.objects.all()
    
    if query:
        members = members.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(member_id__icontains=query)
        )
    
    members = members[:10]  # Limit to 10 results
    
    results = []
    for member in members:
        # Get current borrowed books count
        borrowed_count = Transaction.objects.filter(
            member=member,
            return_date__isnull=True
        ).count()
        
        results.append({
            'id': member.id,
            'name': member.name,
            'member_id': member.member_id,
            'email': member.email,
            'borrowed_count': borrowed_count,
            'can_borrow': borrowed_count < 5  # Assuming max 5 books
        })
    
    return JsonResponse({'results': results})
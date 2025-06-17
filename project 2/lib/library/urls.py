from django.urls import path
from . import views
app_name='library'

urlpatterns=[
    path('',views.home,name='home'),
    path('books/', views.book_list, name='book_list'),    # Book list page
    path('books/add/', views.add_book, name='add_book'),  # Add book
    path('books/<int:pk>/', views.book_detail, name='book_detail'),  # Book details
    path('members/', views.member_list, name='member_list'),  # Members
    path('transactions/', views.transaction_list, name='transaction_list'),  # Transactions
    path('reports/', views.reports, name='reports'),      # Reports
    path('login/', views.login_view, name='login'),       # Login
    path('signup/', views.signup_view, name='signup'),
    path('logout/',views.logout_view,name='logout'),
    path('add_member/',views.add_member,name='add_member'),
    path('checkout_book/',views.checkout_book,name='checkout_book'),
    path('return_book/',views.return_book,name='return_book'),
    path('overdue_books/',views.overdue_books,name='overdue_books'),
    path('reports/',views.reports,name='reports'),

]
from django.urls import path
from . import views
urlpatterns=[
    path('',views.home,name='home'),
    path('books/', views.book_list, name='book-list'),
]
from django.shortcuts import render
from .models import Book
from django.http import HttpResponse

def home(request):
     return render(request,'library/home.html')
    
def book_list(request):
     books=Book.object.all()
     return render(request,'library/book_list.html',{'books':books})
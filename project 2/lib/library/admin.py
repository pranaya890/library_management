from django.contrib import admin
from .models import Book, Member, Transaction, Fine

admin.site.register(Book)
admin.site.register(Member)
admin.site.register(Transaction)
admin.site.register(Fine)

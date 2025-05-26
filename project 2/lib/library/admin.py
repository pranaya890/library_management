from django.contrib import admin
from .models import Member
from .models import Book
from .models import Issue,Category,Fine,ActivityLog 

admin.site.register(Member)
admin.site.register(Book)
admin.site.register(Issue)
admin.site.register(Category)
admin.site.register(Fine)
admin.site.register(ActivityLog)
# Register your models here.

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import Book, Member
import re


class BookForm(forms.ModelForm):
    """Form for adding and editing books in the library system"""
    
    # Custom widget attributes for better UI
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter book title',
            'required': True
        })
    )
    
    author = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter author name',
            'required': True
        })
    )
    
    isbn = forms.CharField(
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ISBN (e.g., 978-0-123456-78-9)',
            'pattern': r'^\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1}$'
        }),
        validators=[
            RegexValidator(
                regex=r'^\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1}$',
                message='Enter a valid ISBN format (e.g., 978-0-123456-78-9)'
            )
        ],
        required=False
    )
    
    publication_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    
    publisher = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter publisher name'
        }),
        required=False
    )
    
    category = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter book category (e.g., Fiction, Science, History)'
        }),
        required=False
    )
    
    total_copies = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter total number of copies',
            'min': '1'
        })
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter book description (optional)',
            'rows': 4
        }),
        required=False
    )

    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publication_date', 'publisher', 
                 'category', 'total_copies', 'description']

    def clean_isbn(self):
        """Custom validation for ISBN"""
        isbn = self.cleaned_data.get('isbn')
        if isbn:
            # Remove hyphens for validation
            isbn_digits = isbn.replace('-', '')
            if not isbn_digits.isdigit() or len(isbn_digits) != 13:
                raise ValidationError('ISBN must contain exactly 13 digits')
        return isbn

    def clean_title(self):
        """Custom validation for title"""
        title = self.cleaned_data.get('title')
        if title:
            title = title.strip()
            if len(title) < 2:
                raise ValidationError('Title must be at least 2 characters long')
        return title

    def clean_total_copies(self):
        """Custom validation for total copies"""
        total_copies = self.cleaned_data.get('total_copies')
        if total_copies and total_copies < 1:
            raise ValidationError('Total copies must be at least 1')
        return total_copies


class MemberForm(forms.ModelForm):
    """Form for adding and editing library members"""
    
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name',
            'required': True
        })
    )
    
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'required': True
        })
    )
    
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number',
            'pattern': r'^\+?[\d\s\-\(\)]+$'
        }),
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message='Enter a valid phone number'
            )
        ]
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter complete address',
            'rows': 3
        })
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    
    membership_type = forms.ChoiceField(
        choices=[
            ('student', 'Student'),
            ('faculty', 'Faculty'),
            ('general', 'General Public'),
            ('senior', 'Senior Citizen')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    emergency_contact_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter emergency contact name'
        }),
        required=False
    )
    
    emergency_contact_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter emergency contact phone'
        }),
        required=False
    )

    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 
                 'date_of_birth', 'membership_type', 'emergency_contact_name', 
                 'emergency_contact_phone']

    def clean_email(self):
        """Custom validation for email uniqueness"""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists (excluding current instance if editing)
            queryset = Member.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError('A member with this email already exists')
        return email

    def clean_phone(self):
        """Custom validation for phone number"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove spaces, hyphens, and parentheses
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
            if not cleaned_phone.replace('+', '').isdigit():
                raise ValidationError('Phone number can only contain digits, spaces, hyphens, and parentheses')
            if len(cleaned_phone.replace('+', '')) < 10:
                raise ValidationError('Phone number must be at least 10 digits long')
        return phone

    def clean_date_of_birth(self):
        """Custom validation for date of birth"""
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            from datetime import date
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 5:
                raise ValidationError('Member must be at least 5 years old')
            if age > 120:
                raise ValidationError('Please enter a valid date of birth')
        return dob

    def clean(self):
        """Form-wide validation"""
        cleaned_data = super().clean()
        
        # If emergency contact name is provided, phone should also be provided
        emergency_name = cleaned_data.get('emergency_contact_name')
        emergency_phone = cleaned_data.get('emergency_contact_phone')
        
        if emergency_name and not emergency_phone:
            raise ValidationError('Emergency contact phone is required when emergency contact name is provided')
        
        if emergency_phone and not emergency_name:
            raise ValidationError('Emergency contact name is required when emergency contact phone is provided')
        
        return cleaned_data


# Additional utility form for searching
class BookSearchForm(forms.Form):
    """Form for searching books"""
    
    search_query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, author, or ISBN...',
        }),
        required=False
    )
    
    category = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by category...',
        }),
        required=False
    )
    
    availability = forms.ChoiceField(
        choices=[
            ('', 'All Books'),
            ('available', 'Available Only'),
            ('borrowed', 'Currently Borrowed')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False
    )


class MemberSearchForm(forms.Form):
    """Form for searching members"""
    
    search_query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or member ID...',
        }),
        required=False
    )
    
    membership_type = forms.ChoiceField(
        choices=[
            ('', 'All Members'),
            ('student', 'Students'),
            ('faculty', 'Faculty'),
            ('general', 'General Public'),
            ('senior', 'Senior Citizens')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        required=False
    )
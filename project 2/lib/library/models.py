
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.urls import reverse
from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from django.db import transaction as db_transaction



class Category(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Category name (must be unique)"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Optional description of the category"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when category was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when category was last updated"
    )
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Custom validation"""
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({'name': 'Category name cannot be empty or just whitespace'})
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]


class Author(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Author's full name"
    )
    biography = models.TextField(
        blank=True, 
        null=True,
        help_text="Author's biography"
    )
    birth_date = models.DateField(
        blank=True, 
        null=True,
        help_text="Author's birth date"
    )
    death_date = models.DateField(
        blank=True, 
        null=True,
        help_text="Author's death date (if applicable)"
    )
    nationality = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Author's nationality"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when author was added"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when author was last updated"
    )
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Custom validation"""
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({'name': 'Author name cannot be empty or just whitespace'})
        
        # Validate birth and death dates
        if self.birth_date and self.death_date:
            if self.birth_date >= self.death_date:
                raise ValidationError({
                    'death_date': 'Death date must be after birth date'
                })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_alive(self):
        """Check if author is still alive"""
        return self.death_date is None
    
    @property
    def age_or_age_at_death(self):
        """Calculate current age or age at death"""
        if not self.birth_date:
            return None
        
        from datetime import date
        end_date = self.death_date or date.today()
        age = end_date.year - self.birth_date.year
        
        # Adjust for birthday not yet reached this year
        if end_date.month < self.birth_date.month or \
           (end_date.month == self.birth_date.month and end_date.day < self.birth_date.day):
            age -= 1
        
        return age
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['nationality']),
        ]


class Publisher(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="Publisher's name"
    )
    address = models.TextField(
        blank=True, 
        null=True,
        help_text="Publisher's address"
    )
    website = models.URLField(
        blank=True, 
        null=True,
        help_text="Publisher's website URL"
    )
    contact_email = models.EmailField(
        blank=True, 
        null=True,
        help_text="Publisher's contact email"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Publisher's phone number"
    )
    established_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Year the publisher was established"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when publisher was added"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when publisher was last updated"
    )
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Custom validation"""
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({'name': 'Publisher name cannot be empty or just whitespace'})
        
        # Validate established year
        if self.established_year:
            from datetime import date
            current_year = date.today().year
            if self.established_year > current_year:
                raise ValidationError({
                    'established_year': 'Established year cannot be in the future'
                })
            if self.established_year < 1400:  # Reasonable minimum for book publishing
                raise ValidationError({
                    'established_year': 'Established year seems too early'
                })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]



class Book(models.Model):
    # Book Status Choices
    CONDITION_CHOICES = [
        ('NEW', 'New'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
        ('DAMAGED', 'Damaged'),
    ]
    
    LANGUAGE_CHOICES = [
        ('EN', 'English'),
        ('NE', 'Nepali'),
        ('HI', 'Hindi'),
        ('FR', 'French'),
        ('ES', 'Spanish'),
        ('DE', 'German'),
        ('OTHER', 'Other'),
    ]
    
    # Basic Information - MIGRATION SAFE
    title = models.CharField(
        max_length=300,
        help_text='Book title'
    )
    subtitle = models.CharField(
        max_length=300, 
        blank=True, 
        null=True,
        help_text='Book subtitle (optional)'
    )
    authors = models.ManyToManyField(
        'Author', 
        related_name='books',
        blank=True,  # MIGRATION SAFE: Allow empty M2M
        help_text='Book authors'
    )
    isbn = models.CharField(
        max_length=17,  # Including hyphens: 978-0-123456-78-9
        unique=True,
        blank=True,  # MIGRATION SAFE: Allow blank for existing records
        null=True,   # MIGRATION SAFE: Allow null for existing records
        validators=[
            RegexValidator(
                regex=r'^(\d{10}|\d{13}|97[89]\d{10}|\d{1,5}-\d{1,7}-\d{1,7}-[\dX])$',
                message='Enter a valid ISBN-10 or ISBN-13'
            )
        ],
        help_text='ISBN-10 or ISBN-13 format (optional for migration)'
    )
    
    # Publication Details - MIGRATION SAFE
    publisher = models.ForeignKey(
        'Publisher', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Book publisher'
    )
    publication_date = models.DateField(
        blank=True,  # MIGRATION SAFE: Allow blank
        null=True,   # MIGRATION SAFE: Allow null
        help_text='Date when book was published'
    )
    edition = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text='Book edition (e.g., "1st Edition", "Revised")'
    )
    pages = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], 
        blank=True,  # MIGRATION SAFE: Allow blank
        null=True,   # MIGRATION SAFE: Allow null
        help_text='Number of pages'
    )
    language = models.CharField(
        max_length=10, 
        choices=LANGUAGE_CHOICES, 
        default='EN',
        help_text='Book language'
    )
    
    # Content Information - MIGRATION SAFE
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text='Brief description of the book'
    )
    category = models.ForeignKey(
        'Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='books',
        help_text='Book category'
    )
    keywords = models.CharField(
        max_length=500, 
        blank=True, 
        null=True, 
        help_text='Comma-separated keywords'
    )
    
    # Physical Information - MIGRATION SAFE
    total_copies = models.PositiveIntegerField(
        default=1, 
        validators=[MinValueValidator(1)],
        help_text='Total number of copies owned'
    )
    available_copies = models.PositiveIntegerField(
        default=1, 
        validators=[MinValueValidator(0)],
        help_text='Number of copies available for borrowing'
    )
    condition = models.CharField(
        max_length=10, 
        choices=CONDITION_CHOICES, 
        default='GOOD',
        help_text='Physical condition of the book'
    )
    location = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text='Shelf location (e.g., A-12-3)'
    )
    
    # Price and Acquisition - MIGRATION SAFE
    purchase_price = models.DecimalField(
        max_digits=10,  # Increased for larger amounts
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price paid for the book'
    )
    purchase_date = models.DateField(
        blank=True, 
        null=True,
        help_text='Date when book was purchased'
    )
    
    # System Information - MIGRATION SAFE
    added_date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date and time when book was added to system'
    )
    updated_date = models.DateTimeField(
        auto_now=True,
        help_text='Date and time when book was last updated'
    )
    is_active = models.BooleanField(
        default=True, 
        help_text='Uncheck to remove from circulation'
    )
    
    # Additional fields for better library management
    barcode = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text='Library barcode for the book'
    )
    acquisition_method = models.CharField(
        max_length=20,
        choices=[
            ('PURCHASE', 'Purchase'),
            ('DONATION', 'Donation'),
            ('EXCHANGE', 'Exchange'),
            ('OTHER', 'Other'),
        ],
        default='PURCHASE',
        help_text='How the book was acquired'
    )
    
    def __str__(self):
        authors_str = ", ".join([author.name for author in self.authors.all()])
        if authors_str:
            return f"{self.title} by {authors_str}"
        return self.title
    
    def get_absolute_url(self):
        return reverse('book_detail', kwargs={'pk': self.pk})
    
    @property
    def is_available(self):
        """Check if book is available for borrowing"""
        return self.available_copies > 0 and self.is_active
    
    @property
    def borrowed_copies(self):
        """Calculate number of copies currently borrowed"""
        return max(0, self.total_copies - self.available_copies)
    
    @property
    def authors_list(self):
        """Get comma-separated list of authors"""
        return ", ".join([author.name for author in self.authors.all()])
    
    @property
    def is_new_arrival(self):
        """Check if book was added in last 30 days"""
        from datetime import timedelta
        return (date.today() - self.added_date.date()) <= timedelta(days=30)
    
    @property
    def publication_year(self):
        """Get publication year"""
        return self.publication_date.year if self.publication_date else None
    
    def clean(self):
        """Custom validation"""
        errors = {}
        
        # Ensure available copies don't exceed total copies
        if self.available_copies and self.total_copies and self.available_copies > self.total_copies:
            errors['available_copies'] = 'Available copies cannot exceed total copies.'
        
        # Ensure publication date is not in the future
        if self.publication_date and self.publication_date > date.today():
            errors['publication_date'] = 'Publication date cannot be in the future.'
        
        # Ensure purchase date is not in the future
        if self.purchase_date and self.purchase_date > date.today():
            errors['purchase_date'] = 'Purchase date cannot be in the future.'
        
        # Validate ISBN uniqueness only if provided
        if self.isbn:
            # Clean ISBN (remove spaces and hyphens for validation)
            clean_isbn = self.isbn.replace('-', '').replace(' ', '')
            if len(clean_isbn) not in [10, 13]:
                errors['isbn'] = 'ISBN must be 10 or 13 digits long.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Auto-set available_copies to total_copies for new books
        if not self.pk and self.total_copies:
            if not self.available_copies or self.available_copies == 1:
                self.available_copies = self.total_copies
        
        # Ensure minimum values
        if not self.total_copies:
            self.total_copies = 1
        if self.available_copies is None:
            self.available_copies = self.total_copies
        
        # Call clean method before saving
        self.clean()
        super().save(*args, **kwargs)
    
    def add_copies(self, count):
        """Add more copies of this book"""
        if count <= 0:
            raise ValueError("Count must be positive")
        
        self.total_copies += count
        self.available_copies += count
        self.save()
        return f"Added {count} copies. Total: {self.total_copies}"
    
    def remove_copies(self, count):
        """Remove copies of this book"""
        if count <= 0:
            raise ValueError("Count must be positive")
        
        if count > self.available_copies:
            raise ValueError("Cannot remove more copies than available")
        
        self.total_copies -= count
        self.available_copies -= count
        self.save()
        return f"Removed {count} copies. Total: {self.total_copies}"
    
    class Meta:
        ordering = ['title', 'publication_date']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['isbn']),
            models.Index(fields=['publication_date']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['barcode']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(available_copies__lte=models.F('total_copies')),
                name='available_copies_not_exceed_total'
            ),
            models.CheckConstraint(
                check=models.Q(total_copies__gte=1),
                name='total_copies_minimum_one'
            ),
        ]


class BookCopy(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    copy_number = models.PositiveIntegerField(default=1)

    condition = models.CharField(max_length=10, choices=Book.CONDITION_CHOICES, default='GOOD')
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.book.title} - Copy #{self.copy_number}"
    
    class Meta:
        unique_together = ['book', 'copy_number']
        ordering = ['book', 'copy_number']
        verbose_name = 'Book Copy'
        verbose_name_plural = 'Book Copies'





class Member(models.Model):
    # Membership Type Choices
    MEMBERSHIP_TYPES = [
        ('STUDENT', 'Student'),
        ('STAFF', 'Staff'),
        ('GENERAL', 'General Public'),
    ]
    
    # Status Choices
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('EXPIRED', 'Expired'),
    ]
    
    # User Information (One-to-One with Django User)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='member_profile',
        null=True,
        blank=True,
        help_text='Associated user account'
    )
    
    # Member Identification
    member_id = models.CharField(
        max_length=20, 
        unique=True,
        help_text='Unique library member ID (e.g., LIB2024001)',
        null=True,  # Added to avoid migration issues
        blank=True  # Added to avoid migration issues
    )
    
    # Contact Information
    phone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Enter a valid phone number (9-15 digits)'
            )
        ],
        null=True,  # Changed from default to nullable
        blank=True
    )
    alternate_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Enter a valid phone number (9-15 digits)'
            )
        ]
    )
    
    # Address Information
    address_line1 = models.CharField(max_length=200, null=True, blank=True)  # Changed from default to nullable
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, null=True, blank=True)  # Changed from default to nullable
    state_province = models.CharField(max_length=100, null=True, blank=True)  # Changed from default to nullable
    postal_code = models.CharField(max_length=20, null=True, blank=True)  # Changed from default to nullable
    country = models.CharField(max_length=100, default='Nepal')
    
    # Membership Details
    membership_type = models.CharField(
        max_length=20, 
        choices=MEMBERSHIP_TYPES, 
        default='GENERAL'
    )
    membership_date = models.DateField(auto_now_add=True)
    membership_expiry = models.DateField(
        help_text='Membership expiration date',
        null=True,  # Made nullable to avoid lambda issues
        blank=True
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE'
    )
    
    # Library Privileges
    max_books_allowed = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        help_text='Maximum number of books this member can borrow'
    )
    max_days_allowed = models.PositiveIntegerField(
        default=14,
        validators=[MinValueValidator(1)],
        help_text='Maximum days to keep borrowed books'
    )
    
    # Financial Information
    security_deposit = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        help_text='Security deposit paid by member'
    )
    outstanding_fines = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00,
        help_text='Total unpaid fines'
    )
    
    # Additional Information
    occupation = models.CharField(max_length=100, blank=True, null=True)
    institution = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text='School/College/Organization name'
    )
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)  # Changed from default to nullable
    emergency_contact_phone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Enter a valid phone number'
            )
        ],
        null=True,  # Changed from default to nullable
        blank=True
    )
    
    # System Fields
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text='Internal notes about this member'
    )
    
    def __str__(self):
        if self.user:
            return f"{self.user.get_full_name()} ({self.member_id or 'No ID'})"
        return f"Member {self.member_id or 'No ID'}"
    
    def get_full_name(self):
        """Get member's full name"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return "Unknown Member"
    
    def get_full_address(self):
        """Get formatted full address"""
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state_province,
            self.postal_code,
            self.country
        ]
        return ", ".join([part for part in address_parts if part])
    
    @property
    def is_membership_expired(self):
        """Check if membership has expired"""
        if self.membership_expiry:
            return self.membership_expiry < date.today()
        return False
    
    @property
    def days_until_expiry(self):
        """Calculate days until membership expires"""
        if self.membership_expiry:
            delta = self.membership_expiry - date.today()
            return delta.days
        return None
    
    @property
    def is_active_member(self):
        """Check if member can use library services"""
        return (
            self.status == 'ACTIVE' and 
            not self.is_membership_expired and
            self.outstanding_fines < 500.00  # Assuming 500 is the limit
        )
    
    @property
    def current_borrowed_books_count(self):
        """Get count of currently borrowed books"""
        from .models import Transaction  # Import here to avoid circular import
        return Transaction.objects.filter(
            member=self,
            transaction_type='BORROW',
            return_date__isnull=True
        ).count()
    
    @property
    def can_borrow_more_books(self):
        """Check if member can borrow more books"""
        return (
            self.is_active_member and 
            self.current_borrowed_books_count < self.max_books_allowed
        )
    
    @property
    def available_book_slots(self):
        """Get number of additional books member can borrow"""
        if self.can_borrow_more_books:
            return self.max_books_allowed - self.current_borrowed_books_count
        return 0
    
    def clean(self):
        """Custom validation"""
        # Ensure membership expiry is not in the past for new members
        if not self.pk and self.membership_expiry and self.membership_expiry <= date.today():
            raise ValidationError({
                'membership_expiry': 'Membership expiry date must be in the future.'
            })
        
        # Ensure max_books_allowed is reasonable
        if self.max_books_allowed > 20:
            raise ValidationError({
                'max_books_allowed': 'Maximum books allowed cannot exceed 20.'
            })
        
        # Emergency contact cannot be the same as member's phone
        if (self.emergency_contact_phone and self.phone and 
            self.emergency_contact_phone == self.phone):
            raise ValidationError({
                'emergency_contact_phone': 'Emergency contact must be different from member phone.'
            })
    
    def save(self, *args, **kwargs):
        # Auto-generate member_id if not provided
        if not self.member_id:
            # Generate member ID based on year and count
            year = date.today().year
            last_member = Member.objects.filter(
                member_id__startswith=f'LIB{year}'
            ).order_by('-member_id').first()
            
            if last_member:
                try:
                    last_number = int(last_member.member_id[-3:])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.member_id = f'LIB{year}{new_number:03d}'
        
        # Auto-set membership expiry based on type if not provided
        if not self.membership_expiry:
            if self.membership_type == 'STUDENT':
                self.membership_expiry = date.today() + timedelta(days=365)  # 1 year
            elif self.membership_type == 'STAFF':
                self.membership_expiry = date.today() + timedelta(days=1095)  # 3 years
            else:  # GENERAL
                self.membership_expiry = date.today() + timedelta(days=365)  # 1 year
        
        # Set max_books_allowed based on membership type
        if not self.pk:  # Only for new members
            if self.membership_type == 'STUDENT':
                self.max_books_allowed = 3
            elif self.membership_type == 'STAFF':
                self.max_books_allowed = 8
            else:  # GENERAL
                self.max_books_allowed = 5
        
        # Call clean method
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['user__last_name', 'user__first_name', 'member_id']
        verbose_name = 'Library Member'
        verbose_name_plural = 'Library Members'
        indexes = [
            models.Index(fields=['member_id']),
            models.Index(fields=['phone']),
            models.Index(fields=['membership_type']),
            models.Index(fields=['status']),
            models.Index(fields=['membership_expiry']),
        ]


@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    """Automatically create Member profile when User is created"""
    if created:
        Member.objects.create(user=instance)

# below here
class Transaction(models.Model):
    """
    Model to track book borrowing and returning transactions
    """
    
    TRANSACTION_STATUS = [
        ('BORROWED', 'Borrowed'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
        ('LOST', 'Lost'),
    ]
    
    # Core Information
    book = models.ForeignKey(
        'Book',  # Reference to Book model
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    member = models.ForeignKey(
        'Member',  # Reference to Member model
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Transaction Details
    transaction_id = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique transaction ID (auto-generated)',
        null=True,  # Added to avoid migration issues
        blank=True  # Added to avoid migration issues
    )
    
    # Dates
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(
        help_text='Date when book should be returned',
        null=True,  # Made nullable to avoid lambda issues
        blank=True
    )
    return_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual return date (null if not returned)'
    )
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default='BORROWED'
    )
    
    # Renewal Information
    renewal_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of times this transaction has been renewed'
    )
    max_renewals_allowed = models.PositiveIntegerField(
        default=2,
        help_text='Maximum renewals allowed for this transaction'
    )
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes about this transaction'
    )
    
    def __str__(self):
        book_title = self.book.title if self.book else "Unknown Book"
        member_name = self.member.get_full_name() if self.member else "Unknown Member"
        transaction_id = self.transaction_id or "No ID"
        return f"{transaction_id} - {book_title} by {member_name}"
    
    @property
    def is_overdue(self):
        """Check if the book is overdue"""
        if self.status == 'RETURNED' or not self.due_date:
            return False
        return date.today() > self.due_date
    
    @property
    def days_overdue(self):
        """Calculate how many days overdue"""
        if not self.is_overdue or not self.due_date:
            return 0
        return (date.today() - self.due_date).days
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.status == 'RETURNED' or not self.due_date:
            return 0
        return (self.due_date - date.today()).days
    
    @property
    def can_renew(self):
        """Check if transaction can be renewed"""
        return (
            self.status == 'BORROWED' and
            self.renewal_count < self.max_renewals_allowed and
            not self.is_overdue and
            self.member.is_active_member
        )
    
    @property
    def calculated_fine(self):
        """Calculate fine amount based on overdue days"""
        if not self.is_overdue:
            return Decimal('0.00')
        
        # Fine calculation: 5 rupees per day overdue
        fine_per_day = Decimal('5.00')
        return fine_per_day * self.days_overdue
    
    def renew_transaction(self, days=14):
        """Renew the transaction for additional days"""
        if not self.can_renew:
            raise ValidationError("Transaction cannot be renewed")
        
        if not self.due_date:
            raise ValidationError("Cannot renew transaction without due date")
        
        self.due_date = self.due_date + timedelta(days=days)
        self.renewal_count += 1
        self.save()
        
        return f"Transaction renewed until {self.due_date}"
    
    def return_book(self):
        """Mark book as returned and update availability"""
        if self.status == 'RETURNED':
            raise ValidationError("Book is already returned")
        
        self.return_date = date.today()
        self.status = 'RETURNED'
        
        # Update book availability
        self.book.available_copies += 1
        self.book.save()
        
        # Create fine if overdue
        if self.is_overdue:
            fine_amount = self.calculated_fine
            # Import Fine model here to avoid circular imports
            from .models import Fine
            Fine.objects.create(
                transaction=self,
                member=self.member,
                fine_amount=fine_amount,
                reason=f"Overdue return - {self.days_overdue} days late"
            )
        
        self.save()
        return f"Book returned successfully"
    
    def clean(self):
        """Custom validation"""
        # Due date should be after borrow date
        if self.due_date and self.due_date <= self.borrow_date:
            raise ValidationError({
                'due_date': 'Due date must be after borrow date'
            })
        
        # Return date should not be before borrow date
        if self.return_date and self.return_date < self.borrow_date:
            raise ValidationError({
                'return_date': 'Return date cannot be before borrow date'
            })
        
        # Check member borrowing limit
        if not self.pk:  # New transaction
            current_borrowed = Transaction.objects.filter(
                member=self.member,
                status='BORROWED'
            ).count()
            
            if current_borrowed >= self.member.max_books_allowed:
                raise ValidationError(
                    f"Member has reached maximum borrowing limit of {self.member.max_books_allowed} books"
                )
    
    def save(self, *args, **kwargs):
        # Auto-generate transaction ID
        if not self.transaction_id:
            year = date.today().year
            month = date.today().month
            last_transaction = Transaction.objects.filter(
                transaction_id__startswith=f'T{year}{month:02d}'
            ).order_by('-transaction_id').first()
            
            if last_transaction:
                try:
                    last_number = int(last_transaction.transaction_id[-4:])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.transaction_id = f'T{year}{month:02d}{new_number:04d}'
        
        # Set due date based on member's allowed days if not set
        if not self.due_date:
            member_days = getattr(self.member, 'max_days_allowed', 14)
            self.due_date = self.borrow_date + timedelta(days=member_days)
        
        # Update status based on dates
        if self.return_date:
            self.status = 'RETURNED'
        elif self.is_overdue and self.status == 'BORROWED':
            self.status = 'OVERDUE'
        
        # Update book availability for new borrowing
        if not self.pk and self.status == 'BORROWED':
            if self.book.available_copies <= 0:
                raise ValidationError("Book is not available for borrowing")
            self.book.available_copies -= 1
            self.book.save()
        
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-borrow_date', '-created_at']
        verbose_name = 'Book Transaction'
        verbose_name_plural = 'Book Transactions'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['borrow_date']),
            models.Index(fields=['member', 'status']),
        ]

class Fine(models.Model):
    """
    Model to track fines for overdue books and other penalties
    """
    
    FINE_STATUS = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('WAIVED', 'Waived'),
        ('PARTIAL', 'Partially Paid'),
    ]
    
    FINE_REASONS = [
        ('OVERDUE', 'Overdue Return'),
        ('DAMAGE', 'Book Damage'),
        ('LOST', 'Lost Book'),
        ('OTHER', 'Other'),
    ]
    
    # Core Information
    transaction = models.ForeignKey(
        'Transaction',
        on_delete=models.CASCADE,
        related_name='fines',
        null=True,
        blank=True,
        help_text='Related transaction (if applicable)'
    )
    
    # Make member nullable to handle existing data during migrations
    member = models.ForeignKey(
        'Member',
        on_delete=models.CASCADE,
        related_name='fines',
        null=True,  # Allow null during migration
        blank=True,  # Allow blank in forms
        help_text='Member who owes the fine'
    )
    
    # Fine Details
    fine_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text='Unique fine ID (auto-generated)',
        null=True,  # Added to avoid migration issues
        blank=True  # Added to avoid migration issues
    )
    fine_amount = models.DecimalField(
        max_digits=10,  # Increased for larger amounts
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Total fine amount',
        null=True,  # Made nullable to avoid migration issues
        blank=True
    )
    reason = models.CharField(
        max_length=20,
        choices=FINE_REASONS,
        default='OVERDUE',
        db_index=True
    )
    reason_description = models.TextField(
        help_text='Detailed description of the fine reason',
        null=True,  # Made nullable to avoid migration issues
        blank=True
    )
    
    # Payment Information
    status = models.CharField(
        max_length=20,
        choices=FINE_STATUS,
        default='UNPAID',
        db_index=True
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Dates
    fine_date = models.DateField(
        auto_now_add=True,
        db_index=True
    )
    payment_date = models.DateField(
        null=True, 
        blank=True,
        help_text='Date when fine was fully paid or waived'
    )
    due_date = models.DateField(
        help_text='Date by which fine should be paid',
        db_index=True,
        null=True,  # Made nullable to avoid migration issues
        blank=True
    )
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional Information
    collected_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Staff member who collected the fine'
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text='Additional notes about the fine'
    )
    
    # Add fields for better tracking
    waived_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Staff member who waived the fine'
    )
    waived_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason for waiving the fine'
    )

    class Meta:
        ordering = ['-fine_date', '-created_at']
        verbose_name = 'Library Fine'
        verbose_name_plural = 'Library Fines'
        indexes = [
            models.Index(fields=['fine_id']),
            models.Index(fields=['status']),
            models.Index(fields=['fine_date']),
            models.Index(fields=['due_date']),
            models.Index(fields=['member', 'status']),
            models.Index(fields=['reason']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount_paid__lte=models.F('fine_amount')),
                name='fine_amount_paid_not_exceed_fine_amount'
            ),
            models.CheckConstraint(
                check=models.Q(fine_amount__gt=0),
                name='fine_amount_positive'
            ),
        ]

    def __str__(self):
        member_name = self.member.get_full_name() if self.member else 'Unknown Member'
        fine_id = self.fine_id or 'No ID'
        fine_amount = self.fine_amount or Decimal('0.00')
        return f"{fine_id} - {member_name} - Rs.{fine_amount}"
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to be paid"""
        if not self.fine_amount:
            return Decimal('0.00')
        return max(self.fine_amount - self.amount_paid, Decimal('0.00'))
    
    @property
    def is_fully_paid(self):
        """Check if fine is fully paid"""
        if not self.fine_amount:
            return True
        return self.amount_paid >= self.fine_amount
    
    @property
    def is_overdue_payment(self):
        """Check if fine payment is overdue"""
        if self.status in ['PAID', 'WAIVED'] or not self.due_date:
            return False
        return date.today() > self.due_date
    
    @property
    def days_overdue_payment(self):
        """Calculate days payment is overdue"""
        if not self.is_overdue_payment or not self.due_date:
            return 0
        return (date.today() - self.due_date).days
    
    @db_transaction.atomic
    def make_payment(self, amount, collected_by=None):
        """Record a payment for this fine"""
        if not self.member:
            raise ValidationError("Cannot process payment: No member associated with this fine")
            
        if not self.fine_amount:
            raise ValidationError("Cannot process payment: Fine amount not set")
            
        if self.status == 'PAID':
            raise ValidationError("Fine is already fully paid")
        
        if self.status == 'WAIVED':
            raise ValidationError("Cannot make payment on a waived fine")
        
        amount = Decimal(str(amount))  # Ensure decimal type
        
        if amount <= 0:
            raise ValidationError("Payment amount must be positive")
        
        if self.amount_paid + amount > self.fine_amount:
            raise ValidationError(
                f"Payment amount Rs.{amount} exceeds remaining fine amount Rs.{self.remaining_amount}"
            )
        
        # Record payment
        old_amount_paid = self.amount_paid
        self.amount_paid += amount
        
        if collected_by:
            self.collected_by = collected_by
        
        # Update status
        if self.is_fully_paid:
            self.status = 'PAID'
            self.payment_date = date.today()
        else:
            self.status = 'PARTIAL'
        
        self.save()
        
        # Update member's outstanding fines
        self._update_member_outstanding_fines()
        
        return f"Payment of Rs.{amount} recorded successfully. Remaining: Rs.{self.remaining_amount}"
    
    @db_transaction.atomic
    def waive_fine(self, reason=None, waived_by=None):
        """Waive the fine"""
        if not self.member:
            raise ValidationError("Cannot waive fine: No member associated with this fine")
            
        if self.status == 'PAID':
            raise ValidationError("Cannot waive a fully paid fine")
        
        self.status = 'WAIVED'
        self.payment_date = date.today()
        self.waived_by = waived_by
        self.waived_reason = reason
        
        if reason:
            note = f"Fine waived: {reason}"
            if self.notes:
                self.notes += f"\n{note}"
            else:
                self.notes = note
        
        self.save()
        
        # Update member's outstanding fines
        self._update_member_outstanding_fines()
        
        return "Fine waived successfully"
    
    def _update_member_outstanding_fines(self):
        """Update member's outstanding fines total"""
        if not self.member:
            return
            
        outstanding_total = Fine.objects.filter(
            member=self.member,
            status__in=['UNPAID', 'PARTIAL']
        ).aggregate(
            total=models.Sum(
                models.F('fine_amount') - models.F('amount_paid')
            )
        )['total'] or Decimal('0.00')
        
        # Update member's outstanding fines field if it exists
        if hasattr(self.member, 'outstanding_fines'):
            self.member.outstanding_fines = outstanding_total
            self.member.save(update_fields=['outstanding_fines'])
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount_paid and self.fine_amount and self.amount_paid > self.fine_amount:
            raise ValidationError({
                'amount_paid': 'Amount paid cannot exceed fine amount'
            })
        
        if self.due_date and self.fine_date and self.due_date <= self.fine_date:
            raise ValidationError({
                'due_date': 'Due date must be after fine date'
            })
        
        # Validate status consistency
        if self.status == 'PAID' and not self.is_fully_paid:
            raise ValidationError({
                'status': 'Status cannot be PAID when amount paid is less than fine amount'
            })
    
    def save(self, *args, **kwargs):
        # Auto-generate fine ID if not provided
        if not self.fine_id:
            self.fine_id = self._generate_fine_id()
        
        # Set default fine amount if not provided
        if not self.fine_amount:
            self.fine_amount = Decimal('10.00')  # Default fine amount
        
        # Set due date if not provided (30 days from fine date)
        if not self.due_date:
            if self.fine_date:
                self.due_date = self.fine_date + timedelta(days=30)
            else:
                self.due_date = date.today() + timedelta(days=30)
        
        # Set default reason description if not provided
        if not self.reason_description:
            reason_map = dict(self.FINE_REASONS)
            self.reason_description = reason_map.get(self.reason, 'Fine issued')
        
        # Validate before saving
        self.clean()
        
        # Call parent save
        super().save(*args, **kwargs)
        
        # Update member's outstanding fines after saving
        self._update_member_outstanding_fines()
    
    def _generate_fine_id(self):
        """Generate unique fine ID"""
        today = date.today()
        year = today.year
        month = today.month
        prefix = f'F{year}{month:02d}'
        
        # Get the last fine ID for this month
        last_fine = Fine.objects.filter(
            fine_id__startswith=prefix
        ).order_by('-fine_id').first()
        
        if last_fine and last_fine.fine_id.startswith(prefix):
            try:
                last_number = int(last_fine.fine_id[-4:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f'{prefix}{new_number:04d}'
    
    @classmethod
    def get_overdue_fines(cls, member=None):
        """Get overdue fines"""
        queryset = cls.objects.filter(
            status__in=['UNPAID', 'PARTIAL'],
            due_date__lt=date.today()
        )
        
        if member:
            queryset = queryset.filter(member=member)
        
        return queryset
    
    @classmethod
    def get_member_total_fines(cls, member):
        """Get total fines for a member"""
        return cls.objects.filter(member=member).aggregate(
            total_fines=models.Sum('fine_amount'),
            total_paid=models.Sum('amount_paid'),
            outstanding=models.Sum(
                models.F('fine_amount') - models.F('amount_paid'),
                filter=models.Q(status__in=['UNPAID', 'PARTIAL'])
            )
        )
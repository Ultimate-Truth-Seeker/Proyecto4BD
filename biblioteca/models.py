from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.postgres.fields import ArrayField
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
    EmailValidator,
    ValidationError,
)
from django.utils import timezone

############################
#  Personalised PG types   #
############################
#  ───────────────────────  #
#  Django no crea dominios/ENUMs automáticamente.  #
############################

class BookConditionField(models.Field):
    """Mapea el ENUM PostgreSQL `book_condition`."""

    description = "PostgreSQL ENUM book_condition"

    def db_type(self, connection):
        return "book_condition"

    def from_db_value(self, value, expression, connection):
        return value

    def get_prep_value(self, value):
        return value

class MoneyField(models.Field):
    """Mapea el tipo compuesto `money (amount numeric, currency char(3))`."""

    description = "Composite money"

    def db_type(self, connection):
        return "money"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        amount, currency = value.strip("(){}").split(",")
        return {"amount": amount, "currency": currency}

    def get_prep_value(self, value):
        if value is None:
            return None
        # Espera un dict {"amount": ..., "currency": ...}
        return f"({value['amount']},{value['currency']})"

class RatingScaleField(models.Field):
    """Mapea el ENUM PostgreSQL `rating_scale`."""
    description = "PostgreSQL ENUM rating_scale"
    def db_type(self, connection):
        return "rating_scale"
    def from_db_value(self, value, expression, connection):
        return value
    def get_prep_value(self, value):
        return value

############################
#        Usuarios          #
############################

# biblioteca/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class LibraryUser(models.Model):
    # Campos básicos de usuario
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    password = models.CharField(max_length=128)

    phone_regex = RegexValidator(
        regex=r"^\+?[0-9\-\s]{7,20}$",
        message="Número telefónico inválido",
    )
    phone_number = models.CharField(
        max_length=20, validators=[phone_regex], blank=True, null=True
    )
    birth_date = models.DateField(blank=True, null=True)

    STATUS_CHOICES = [
        ("active", "Activo"),
        ("suspended", "Suspendido"),
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="active"
    )

    # Metadatos
    date_joined = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "library_users"
        constraints = [
            models.CheckConstraint(
                check=models.Q(birth_date__lt=timezone.now().date()),
                name="ck_user_birth_past",
            ),
            models.UniqueConstraint(fields=["email"], name="uq_user_email"),
        ]

    def __str__(self):
        return self.username

    # Métodos para manejar contraseña
    def set_password(self, raw_password):
        """
        Hashea y guarda la contraseña.
        """
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Verifica un password en texto claro contra el hash almacenado.
        """
        return check_password(raw_password, self.password)

############################
#      Autz & Permisos     #
############################

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Permission(models.Model):
    codename = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.codename

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="permission_roles")

    class Meta:
        unique_together = ("role", "permission")

############################
#        Ubicación         #
############################

class Branch(models.Model):
    name = models.CharField(max_length=120, unique=True)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=25, validators=[RegexValidator(r"^\+?[0-9\- ]+$")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Shelf(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="shelves")
    code = models.CharField(max_length=20)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("branch", "code")

    def __str__(self):
        return f"{self.branch.name}-{self.code}"

############################
#         Catálogo         #
############################

class Author(models.Model):
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    birth_year = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(timezone.now().year),
        ]
    )

    class Meta:
        unique_together = ("first_name", "last_name", "birth_year")
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

class Genre(models.Model):
    name = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    isbn = models.CharField(
        max_length=13,
        primary_key=True,
        validators=[RegexValidator(r"^\d{10}(\d{3})?$")],
    )
    title = models.CharField(max_length=255)
    main_author = models.ForeignKey(
        Author, on_delete=models.PROTECT, related_name="primary_books"
    )
    other_authors = models.ManyToManyField(
        Author, through="BookAuthor", related_name="contributed_books"
    )
    genres = models.ManyToManyField(Genre, through="BookGenre")
    published_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1440), MaxValueValidator(timezone.now().year)]
    )
    languages = ArrayField(models.CharField(max_length=30), default=list)  # multivaluado
    condition = BookConditionField(default="good")  # enum personalizado
    page_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["title"])]

    def __str__(self):
        return self.title

    @property
    def total_available(self):  # atributo derivado
        return self.copies.filter(is_available=True).count()

class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("book", "author")

class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("book", "genre")

class Copy(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="copies")
    shelf = models.ForeignKey(Shelf, on_delete=models.SET_NULL, null=True)
    inventory_code = models.CharField(max_length=30, unique=True)
    is_available = models.BooleanField(default=True)
    acquired_at = models.DateField(default=timezone.now)
    price = MoneyField()  # composite type

    class Meta:
        ordering = ["inventory_code"]

    def __str__(self):
        return self.inventory_code

############################
#      Préstamos & +       #
############################

class Loan(models.Model):
    copy = models.ForeignKey(Copy, on_delete=models.PROTECT)
    user = models.ForeignKey(LibraryUser, on_delete=models.PROTECT)
    loaned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(due_date__gt=models.F("loaned_at")),
                name="ck_due_after_loan",
            )
        ]

    def clean(self):  # validación a nivel aplicación
        if self.due_date <= self.loaned_at.date():
            raise ValidationError("La fecha de devolución debe ser posterior a la fecha del préstamo.")

class Reservation(models.Model):
    copy = models.ForeignKey(Copy, on_delete=models.PROTECT)
    user = models.ForeignKey(LibraryUser, on_delete=models.PROTECT)
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = ("copy", "user")

class Fine(models.Model):
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

############################
#      Pagos & Métodos     #
############################

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True)
    details_schema = models.JSONField(default=dict)  # describe campos requeridos

    def __str__(self):
        return self.name

class Payment(models.Model):
    fine = models.ForeignKey(Fine, on_delete=models.PROTECT, related_name="payments")
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = MoneyField()
    paid_at = models.DateTimeField(auto_now_add=True)

############################
#      Eventos & Asist.    #
############################

class Event(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    description = models.TextField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField()

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError("La hora de finalización debe ser posterior a la hora de inicio.")

class EventAttendance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE)
    attended_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "user")

############################
#      Reseñas & Votos     #
############################

class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE)
    rating = RatingScaleField(default='average')
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("book", "user")

class ReviewVote(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(LibraryUser, on_delete=models.CASCADE)
    is_upvote = models.BooleanField()

    class Meta:
        unique_together = ("review", "user")

############################
#          Auditoría       #
############################

class AuditLog(models.Model):
    table_name = models.CharField(max_length=60)
    record_id = models.CharField(max_length=50)
    op = models.CharField(max_length=8)
    changed_at = models.DateTimeField(auto_now_add=True)
    change_user = models.CharField(max_length=150)
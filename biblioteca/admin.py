from django.contrib import admin
from .models import (
    CatalogoLibros, PrestamosUsuarios, ActividadSucursales,
    Book, LibraryUser, Loan, Branch, BookAuthor, BookGenre, Copy, Review
)

# ————————————————————————————————
#  Listados basados en las vistas (solo lectura)
# ————————————————————————————————

@admin.register(CatalogoLibros)
class CatalogoAdmin(admin.ModelAdmin):
    list_display = (
        'isbn','title','autor_principal','rating_promedio','estado_disponibilidad',
    )
    search_fields = ('title','isbn','autor_principal')
    list_filter = ('condition',)
    # deshabilitar adición/edición/borrado
    def has_add_permission(self,   request): return False
    def has_change_permission(self,request, obj=None): return False
    def has_delete_permission(self,request, obj=None): return False

@admin.register(PrestamosUsuarios)
class PrestamosUsuariosAdmin(admin.ModelAdmin):
    list_display = (
        'username','nombre_completo','total_prestamos','prestamos_vencidos','monto_multas_pendientes',
    )
    search_fields = ('username','email')
    list_filter = ('estado_prestamos',)
    def has_add_permission(self,   request): return False
    def has_change_permission(self,request, obj=None): return False
    def has_delete_permission(self,request, obj=None): return False

@admin.register(ActividadSucursales)
class ActividadSucursalesAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_sucursal','total_copias','copias_prestadas','nivel_actividad',
    )
    search_fields = ('nombre_sucursal','address')
    list_filter = ('nivel_actividad',)
    def has_add_permission(self,   request): return False
    def has_change_permission(self,request, obj=None): return False
    def has_delete_permission(self,request, obj=None): return False

# ————————————————————————————————
#  CRUD completo sobre las tablas reales
# ————————————————————————————————

class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1

class BookGenreInline(admin.TabularInline):
    model = BookGenre
    extra = 1

class CopyInline(admin.TabularInline):
    model = Copy
    extra = 1

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0  # si no quieres huecos en blanco

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('isbn','title','main_author','condition','created_at')
    search_fields = ('isbn','title')
    list_filter = ('condition','published_year')
    inlines = [BookAuthorInline, BookGenreInline, CopyInline, ReviewInline]

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id','user','copy','loaned_at','due_date','returned_at')
    search_fields = ('user__username','copy__inventory_code')
    list_filter = ('returned_at',)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('id','name','address','phone','created_at')
    search_fields = ('name','address')

# registra aquí todos los modelos sobre los que necesites create/update/delete
# e.g. LibraryUser, Reservation, Review, Fine, PaymentMethod…

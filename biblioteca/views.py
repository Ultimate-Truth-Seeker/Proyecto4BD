from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView,
    CreateView, UpdateView, DeleteView
)
from .models import CatalogoLibros, PrestamosUsuarios, ActividadSucursales             
from biblioteca.models import Book, Loan, Branch


# 1.1 Índice: lista los libros usando la vista SQL
class CatalogoListView(ListView):
    model = CatalogoLibros
    template_name = "biblioteca/catalogo_list.html"
    context_object_name = "libros"              # en template: {{ libros }}


# 1.2 Detalle (opcional)
class LibroDetailView(DetailView):
    model = CatalogoLibros
    template_name = "biblioteca/libro_detail.html"
    pk_url_kwarg = "isbn"                       # tu PK es isbn
    context_object_name = "libro"


# 1.3 Crear nuevo libro (actúa sobre Book)
class BookCreateView(CreateView):
    model = Book
    fields = [
        "isbn", "title", "published_year",
        "languages", "condition",
        "page_count", "main_author",
        # …otros campos que quieras exponer
    ]
    template_name = "biblioteca/book_form.html"
    success_url = reverse_lazy("catalogo-list")


# 1.4 Editar libro existente
class BookUpdateView(UpdateView):
    model = Book
    fields = [
        "title", "published_year",
        "languages", "condition",
        "page_count", "main_author",
        # …igual que en CreateView
    ]
    template_name = "biblioteca/book_form.html"
    success_url = reverse_lazy("catalogo-list")
    lookup_field       = "isbn"
    slug_url_kwarg     = "isbn"


# 1.5 Borrar libro
class BookDeleteView(DeleteView):
    model = Book
    template_name = "biblioteca/book_confirm_delete.html"
    success_url = reverse_lazy("catalogo-list")
    lookup_field       = "isbn"
    slug_url_kwarg     = "isbn"

# 1) Lista de usuarios con su estado de préstamos
class PrestamosUsuariosListView(ListView):
    model = PrestamosUsuarios
    template_name = "biblioteca/prestamos_list.html"
    context_object_name = "usuarios"


# 2) (Opcional) Detalle de un usuario concreto
class PrestamosUsuarioDetailView(DetailView):
    model = PrestamosUsuarios
    template_name = "biblioteca/prestamos_detail.html"
    pk_url_kwarg = "usuario_id"
    context_object_name = "usuario"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # traemos los préstamos reales de Loan para ese usuario
        ctx["loans"] = Loan.objects.filter(user_id=self.object.usuario_id)
        return ctx


# 3) Crear un nuevo préstamo
class LoanCreateView(CreateView):
    model = Loan
    fields = [
        "due_date", "returned_at",
        "copy", "user",
    ]
    template_name = "biblioteca/loan_form.html"
    success_url = reverse_lazy("prestamos-list")


# 4) Editar un préstamo existente
class LoanUpdateView(UpdateView):
    model = Loan
    fields = [
        "due_date", "returned_at",
        "copy", "user",
    ]
    template_name = "biblioteca/loan_form.html"
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("prestamos-list")


# 5) Borrar un préstamo
class LoanDeleteView(DeleteView):
    model = Loan
    template_name = "biblioteca/loan_confirm_delete.html"
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("prestamos-list")

# 1) Lista de todas las sucursales con su actividad
class SucursalesListView(ListView):
    model = ActividadSucursales
    template_name = "biblioteca/sucursales_list.html"
    context_object_name = "sucursales"


# 2) Detalle de una sucursal concreta
class SucursalDetailView(DetailView):
    model = ActividadSucursales
    template_name = "biblioteca/sucursal_detail.html"
    pk_url_kwarg = "sucursal_id"
    context_object_name = "sucursal"


# 3) Crear una nueva sucursal (Branch)
class BranchCreateView(CreateView):
    model = Branch
    fields = ["name", "address", "phone"]
    template_name = "biblioteca/branch_form.html"
    success_url = reverse_lazy("sucursales-list")


# 4) Editar sucursal existente
class BranchUpdateView(UpdateView):
    model = Branch
    fields = ["name", "address", "phone"]
    template_name = "biblioteca/branch_form.html"
    success_url = reverse_lazy("sucursales-list")
    # usa por defecto pk para buscar la sucursal


# 5) Borrar sucursal
class BranchDeleteView(DeleteView):
    model = Branch
    template_name = "biblioteca/branch_confirm_delete.html"
    success_url = reverse_lazy("sucursales-list")
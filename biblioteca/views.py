from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView,
    CreateView, UpdateView, DeleteView
)
from .models import CatalogoLibros, PrestamosUsuarios, ActividadSucursales             
from biblioteca.models import Book, Loan, Branch
from django.http import HttpResponse
from django.db.models import Count, Avg, Q
from django.db import connection
import csv, json

# 1.1 Índice: lista los libros usando la vista SQL
class CatalogoListView(ListView):
    model = CatalogoLibros
    template_name = "biblioteca/catalogo_list.html"
    context_object_name = "libros"


# 1.2 Detalle (opcional)
class LibroDetailView(DetailView):
    model = CatalogoLibros
    template_name = "biblioteca/libro_detail.html"
    pk_url_kwarg = "isbn"
    context_object_name = "libro"


# 1.3 Crear nuevo libro (actúa sobre Book)
class BookCreateView(CreateView):
    model = Book
    fields = [
        "isbn", "title", "published_year",
        "languages", "condition",
        "page_count", "main_author",
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


# 2) Detalle de un usuario concreto
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
        "due_date", #"returned_at",
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


# 5) Borrar sucursal
class BranchDeleteView(DeleteView):
    model = Branch
    template_name = "biblioteca/branch_confirm_delete.html"
    success_url = reverse_lazy("sucursales-list")

# REPORTES

class CatalogoReportView(ListView):
    model = CatalogoLibros
    template_name = "biblioteca/catalogo_report.html"
    context_object_name = "libros"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.GET
        if params.get('year_min'):
            qs = qs.filter(published_year__gte=params['year_min'])
        if params.get('year_max'):
            qs = qs.filter(published_year__lte=params['year_max'])
        if params.get('condition'):
            qs = qs.filter(condition=params['condition'])
        if params.get('genero'):
            qs = qs.filter(generos__icontains=params['genero'])
        if params.get('estado'):
            qs = qs.filter(estado_disponibilidad=params['estado'])
        if params.get('min_rating'):
            qs = qs.filter(rating_promedio__gte=params['min_rating'])
        return qs

    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            qs = self.get_queryset()
            resp = HttpResponse(content_type='text/csv')
            resp['Content-Disposition'] = 'attachment; filename="catalogo_libros.csv"'
            writer = csv.writer(resp)
            writer.writerow([
                'ISBN','Título','Autor','Año','Condición',
                'Páginas','Géneros','Otros Autores',
                'Total Copias','Disponibles','Reviews',
                'Rating','Estado'
            ])
            for b in qs:
                writer.writerow([
                    b.isbn, b.title, b.autor_principal, b.published_year,
                    b.condition, b.page_count, b.generos, b.otros_autores,
                    b.total_copias, b.copias_disponibles, b.total_reviews,
                    b.rating_promedio, b.estado_disponibilidad
                ])
            return resp
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()

        cond_counts = list(
            qs.values('condition')
              .annotate(total=Count('isbn'))
              .order_by('condition')
        )
        disp_counts = list(
            qs.values('estado_disponibilidad')
              .annotate(total=Count('isbn'))
        )

        ctx['cond_labels'] = json.dumps([d['condition'] for d in cond_counts])
        ctx['cond_values'] = json.dumps([d['total']     for d in cond_counts])
        ctx['disp_labels'] = json.dumps([d['estado_disponibilidad'] for d in disp_counts])
        ctx['disp_values'] = json.dumps([d['total']                 for d in disp_counts])

        with connection.cursor() as c:
            c.execute("SELECT unnest(enum_range(NULL::book_condition));")
            enum_vals = [row[0] for row in c.fetchall()]
        ctx['condition_choices'] = [(v, v.title()) for v in enum_vals]
        return ctx
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
        qs = self.request.GET.copy()
        qs.pop('page', None)
        ctx['querystring'] = qs.urlencode()
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

class PrestamosUsuariosReportView(ListView):
    model = PrestamosUsuarios
    template_name = "biblioteca/prestamos_usuarios_report.html"
    context_object_name = "usuarios"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.GET

        # 1. Fecha de alta
        if params.get('joined_from'):
            qs = qs.filter(date_joined__date__gte=params['joined_from'])
        if params.get('joined_to'):
            qs = qs.filter(date_joined__date__lte=params['joined_to'])

        # 2. Estado de préstamos
        if params.get('estado_prestamos'):
            qs = qs.filter(estado_prestamos=params['estado_prestamos'])

        # 3. Préstamos vencidos mínimos
        if params.get('min_vencidos'):
            qs = qs.filter(prestamos_vencidos__gte=params['min_vencidos'])

        # 4. Multas pendientes
        if params.get('min_multas'):
            qs = qs.filter(multas_pendientes__gte=params['min_multas'])

        # 5. Reservas activas como booleano
        if params.get('reservas_activas') == '1':
            qs = qs.filter(reservas_activas__gt=0)
        elif params.get('reservas_activas') == '0':
            qs = qs.filter(reservas_activas=0)

        return qs

    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            qs = self.get_queryset()
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="prestamos_usuarios.csv"'
            writer = csv.writer(response)
            writer.writerow([
                'Usuario ID','Username','Nombre','Email','Estado Usuario',
                'Total Préstamos','Activos','Devueltos','Vencidos',
                'Total Multas','Multas Pendientes','Monto Multas Pendientes',
                'Reservas Totales','Reservas Activas','Reviews','Fecha Alta',
                'Estado Préstamos'
            ])
            for u in qs:
                writer.writerow([
                    u.usuario_id, u.username, u.nombre_completo, u.email, u.estado_usuario,
                    u.total_prestamos, u.prestamos_activos, u.prestamos_devueltos, u.prestamos_vencidos,
                    u.total_multas, u.multas_pendientes, u.monto_multas_pendientes,
                    u.total_reservas, u.reservas_activas, u.total_reviews,
                    u.date_joined.date(), u.estado_prestamos
                ])
            return response
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.request.GET.copy()
        qs.pop('page', None)
        ctx['querystring'] = qs.urlencode()
        qs = self.get_queryset()

        # Distribución por estado de préstamos
        estado_data = list(
            qs.values('estado_prestamos')
              .annotate(count=Count('usuario_id'))
              .order_by('estado_prestamos')
        )
        # Distribución de usuarios con multas pendientes > 0 / = 0
        multas_data = [
            {'label': 'Con Multas Pendientes',    'value': qs.filter(multas_pendientes__gt=0).count()},
            {'label': 'Sin Multas Pendientes',    'value': qs.filter(multas_pendientes=0).count()},
        ]

        # Serializar para JS
        ctx['estado_labels'] = json.dumps([d['estado_prestamos'] for d in estado_data])
        ctx['estado_values'] = json.dumps([d['count']             for d in estado_data])
        ctx['multas_labels'] = json.dumps([d['label'] for d in multas_data])
        ctx['multas_values'] = json.dumps([d['value'] for d in multas_data])

        # Opciones para dropdown de estado_prestamos
        ESTADOS = [ (d['estado_prestamos'], d['estado_prestamos']) for d in estado_data ]
        ctx['estado_prestamos_choices'] = ESTADOS

        return ctx

class ActividadSucursalesReportView(ListView):
    model = ActividadSucursales
    template_name = "biblioteca/actividad_sucursales_report.html"
    context_object_name = "sucursales"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.GET

        # 1. Fecha de creación de sucursal
        if p.get('created_from'):
            qs = qs.filter(created_at__date__gte=p['created_from'])
        if p.get('created_to'):
            qs = qs.filter(created_at__date__lte=p['created_to'])

        # 2. Nivel de actividad
        if p.get('nivel'):
            qs = qs.filter(nivel_actividad=p['nivel'])

        # 3. Mínimo de copias prestadas
        if p.get('min_prestadas'):
            qs = qs.filter(copias_prestadas__gte=p['min_prestadas'])

        # 4. Eventos futuros (booleano)
        if p.get('eventos_futuros') == '1':
            qs = qs.filter(eventos_futuros__gt=0)
        elif p.get('eventos_futuros') == '0':
            qs = qs.filter(eventos_futuros=0)

        # 5. Promedio de asistencia mínimo
        if p.get('min_asistencia'):
            qs = qs.filter(promedio_asistencia_eventos__gte=p['min_asistencia'])

        return qs

    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            qs = self.get_queryset()
            resp = HttpResponse(content_type='text/csv')
            resp['Content-Disposition'] = 'attachment; filename="actividad_sucursales.csv"'
            writer = csv.writer(resp)
            # Cabecera
            writer.writerow([
                'ID','Sucursal','Dirección','Teléfono',
                'Estantes','Total Copias','Prestadas',
                'Préstamos Activos','Vencidos',
                'Eventos Totales','Eventos Futuros','Asistencias',
                '% Ocupación','Prom Asistencia','Fecha Creación',
                'Nivel de Actividad'
            ])
            for s in qs:
                writer.writerow([
                    s.sucursal_id, s.nombre_sucursal, s.address, s.phone,
                    s.total_estantes, s.total_copias, s.copias_prestadas,
                    s.prestamos_activos, s.prestamos_vencidos,
                    s.total_eventos, s.eventos_futuros, s.total_asistencias_eventos,
                    s.porcentaje_ocupacion, s.promedio_asistencia_eventos,
                    s.created_at.date(), s.nivel_actividad
                ])
            return resp
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.request.GET.copy()
        qs.pop('page', None)
        ctx['querystring'] = qs.urlencode()
        qs = self.get_queryset()

        # Distribución por nivel de actividad
        nivel_data = list(
            qs.values('nivel_actividad')
              .annotate(count=Count('sucursal_id'))
              .order_by('nivel_actividad')
        )
        # Distribución de sucursales con/sin eventos futuros
        futuros_data = [
            {'label': 'Con eventos futuros',    'value': qs.filter(eventos_futuros__gt=0).count()},
            {'label': 'Sin eventos futuros',    'value': qs.filter(eventos_futuros=0).count()},
        ]

        # Serializar para Chart.js
        ctx['nivel_labels']   = json.dumps([d['nivel_actividad'] for d in nivel_data])
        ctx['nivel_values']   = json.dumps([d['count']             for d in nivel_data])
        ctx['futuros_labels'] = json.dumps([d['label'] for d in futuros_data])
        ctx['futuros_values'] = json.dumps([d['value'] for d in futuros_data])

        # Choices para el dropdown de nivel_actividad
        ctx['nivel_choices'] = [(d['nivel_actividad'], d['nivel_actividad']) for d in nivel_data]

        return ctx
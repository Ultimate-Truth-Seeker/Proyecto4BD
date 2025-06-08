from django.shortcuts import render
from django.core.paginator import Paginator
from .models import CatalogoLibros, PrestamosUsuarios, ActividadSucursales

def catalogo_libros_view(request):
    """Vista para mostrar el catálogo de libros usando la vista SQL"""
    libros = CatalogoLibros.objects.all()
    
    # Filtros opcionales
    if request.GET.get('genero'):
        libros = libros.filter(generos__icontains=request.GET.get('genero'))
    
    if request.GET.get('disponible'):
        libros = libros.filter(estado_disponibilidad='Disponible')
    
    paginator = Paginator(libros, 25)
    page = request.GET.get('page')
    libros_paginados = paginator.get_page(page)
    
    return render(request, 'biblioteca/catalogo.html', {
        'libros': libros_paginados
    })

def usuarios_prestamos_view(request):
    """Vista para mostrar el estado de préstamos de usuarios"""
    usuarios = PrestamosUsuarios.objects.all()
    
    # Filtros
    if request.GET.get('con_multas'):
        usuarios = usuarios.filter(multas_pendientes__gt=0)
    
    if request.GET.get('con_retrasos'):
        usuarios = usuarios.filter(prestamos_vencidos__gt=0)
    
    return render(request, 'biblioteca/usuarios_prestamos.html', {
        'usuarios': usuarios
    })

def actividad_sucursales_view(request):
    """Vista para mostrar la actividad de sucursales"""
    sucursales = ActividadSucursales.objects.all()
    
    return render(request, 'biblioteca/actividad_sucursales.html', {
        'sucursales': sucursales
    })
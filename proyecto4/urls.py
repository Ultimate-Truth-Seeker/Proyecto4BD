"""
URL configuration for proyecto4 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import biblioteca.views as views

urlpatterns = [
    path('admin/', admin.site.urls),


    # CRUD de Catálogo
    path("catalogo/", views.CatalogoListView.as_view(), name="catalogo-list"),
    path("catalogo/add/", views.BookCreateView.as_view(), name="book-add"),
    path("catalogo/<str:pk>/edit/", views.BookUpdateView.as_view(), name="book-edit"),
    path("catalogo/<str:pk>/delete/", views.BookDeleteView.as_view(), name="book-delete"),
    path("catalogo/<str:isbn>/", views.LibroDetailView.as_view(), name="catalogo-detail"),

    # CRUD de Préstamos
    path("prestamos/", views.PrestamosUsuariosListView.as_view(), name="prestamos-list"),
    path("prestamos/<int:usuario_id>/", views.PrestamosUsuarioDetailView.as_view(), name="prestamos-detail"),
    path("prestamos/add/", views.LoanCreateView.as_view(), name="loan-add"),
    path("prestamos/<int:pk>/edit/", views.LoanUpdateView.as_view(), name="loan-edit"),
    path("prestamos/<int:pk>/delete/", views.LoanDeleteView.as_view(), name="loan-delete"),

    # CRUD de Sucursales
    path("sucursales/", views.SucursalesListView.as_view(), name="sucursales-list"),
    path("sucursales/<int:sucursal_id>/", views.SucursalDetailView.as_view(), name="sucursal-detail"),
    path("sucursales/add/", views.BranchCreateView.as_view(), name="branch-add"),
    path("sucursales/<int:pk>/edit/", views.BranchUpdateView.as_view(), name="branch-edit"),
    path("sucursales/<int:pk>/delete/", views.BranchDeleteView.as_view(), name="branch-delete"),
]

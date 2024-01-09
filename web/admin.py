from django.contrib import admin
from .models import Categoria,Producto
# Register your models here.

admin.site.register(Categoria)
#admin.site.register(Producto)

#decorador para utilizar funciones especiales es lo que se muestra en productos en el panel de administracion
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    #se usa tuplas
    list_display = ('nombre', 'precio', 'categoria', 'fecha_registro')
    list_editable = ('precio',) 
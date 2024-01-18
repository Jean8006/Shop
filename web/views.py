from django.shortcuts import render,get_object_or_404,redirect
from .models import Categoria,Producto
from .carrito import Cart
# Create your views here.
""" VISTAS PARA EL CATALOGO DE PRODUCTOS """
def index(request):
    listaProductos = Producto.objects.all() #mis productos de la base de datos
    listaCategorias = Categoria.objects.all()
    context = {
        'productos':listaProductos,
        'categorias':listaCategorias
    }  
    return render(request, 'index.html',context) 

def productosPorCategoria(request,categoria_id):
    """VISTA PARA FILTRAR PRODUCTOS POR CATEGORIA"""
    objCategoria = Categoria.objects.get(pk=categoria_id) #esta filtrando por el id de categoria
    listaProductos = objCategoria.producto_set.all() #trae un listado de los productos que pertenecen a esa categoria
    
    listaCategorias = Categoria.objects.all()
    
    context = {
        'categorias':listaCategorias,
        'productos':listaProductos
    }
    
    return render(request,'index.html',context)

def productosPorNombre(request):
    """VISTA PARA FILTRADO DE PRODUCTOS POR NOMBRE"""
    nombre = request.POST['nombre'] #traemos por POST un nombre que escribe el usuario
    
    listaProductos = Producto.objects.filter(nombre__contains=nombre) #aqui filtramos para que traiga todos los productos que contengan el nombre solicitado en su nombre
    listaCategorias = Categoria.objects.all()
    
    context = {
        'categorias':listaCategorias,
        'productos':listaProductos
    }
    
    return render(request,'index.html',context)

def productoDetalle(request,producto_id):
    """VISTA PARA EL DETALLE DEL PRODUCTO"""
    
    #objProducto = Producto.objects.get(pk=producto_id)
    objProducto = get_object_or_404(Producto,pk=producto_id) #aqui llama al objeto y si no existe arroja un 404, se filtra mediante el tipo de objeto y el valor que se quiere filtrar en este caso por id
    context = {
        'producto':objProducto
    }
    
    return render(request,'producto.html',context)

"""VISTA PARA EL CARRITO DE COMPRAS"""

def carrito(request):
    return render(request,'carrito.html')

def agregarCarrito(request,producto_id):
    if request.method == 'POST':
        cantidad = int(request.POST['cantidad'])
    else:
        cantidad = 1

    objProducto = Producto.objects.get(pk=producto_id)
    carritoProducto = Cart(request)
    carritoProducto.add(objProducto,cantidad)

    if request.method == "GET":
        return redirect('/')

    return render(request,'carrito.html')

def eliminarProductoCarrito(request, producto_id):
    objProducto = Producto.objects.get(pk=producto_id)
    carritoProducto = Cart(request)
    carritoProducto.delete(objProducto)

    return render(request, "carrito.html")

def limpiarCarrito(request):
    carritoProducto = Cart(request)
    carritoProducto.clear()
    return render(request, "carrito.html")
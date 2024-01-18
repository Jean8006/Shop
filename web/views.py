from django.shortcuts import render,get_object_or_404,redirect
from .models import Categoria,Producto,Cliente
from .carrito import Cart
from django.contrib.auth.models import User
from django.contrib.auth import login,logout,authenticate
from .forms import ClienteForm
from django.contrib.auth.decorators import login_required
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

"""VISTAS PARA CLIENTES Y USUARIOS"""

def crearUsuario(request):
    if request.method == 'POST':
        dataUsuario = request.POST['nuevoUsuario']
        dataPassword = request.POST['nuevoPassword']

        nuevoUsuario = User.objects.create_user(username=dataUsuario,password=dataPassword) #al usar este objeto de django "User" me permite encriptar automaticamente el password
        if nuevoUsuario is not None:
            #si el usuario viene vacio lo que hara es un login en la aplicacion con una sesion
            login(request, nuevoUsuario)
            return redirect("/cuenta")

    return render(request, "login.html")

def loginUsuario(request):
    paginaDestino = request.GET.get('next', None) #captura la variable next que se envia con el pedido, si no existe lo deja en None
    context = {
        'destino':paginaDestino
    }

    if request.method == 'POST':
        dataUsuario = request.POST['usuario']
        dataPassword = request.POST['password']
        dataDestino = request.POST['destino']

        usuarioAuth = authenticate(request,username=dataUsuario,password=dataPassword)
        if usuarioAuth is not None:
            login(request, usuarioAuth)
            if dataDestino != None:
                return redirect(dataDestino)


            return redirect("/cuenta")
        else:
            context = {
                'mensajeError':'Datos incorrectos'
            }

    return render(request,'login.html',context)

def logoutUsuario(request):
    logout(request)
    return render(request,"login.html")

def cuentaUsuario(request):
    
    try:
        clienteEditar = Cliente.objects.get(usuario = request.user)

        dataCliente = {
            'nombre':request.user.first_name,
            'apellidos':request.user.last_name,
            'email':request.user.email,
            'direccion':clienteEditar.direccion,
            'telefono':clienteEditar.telefono,
            'dni':clienteEditar.dni,
            'sexo':clienteEditar.sexo,
            'fecha_nacimiento':clienteEditar.fecha_nacimiento
        }
    except:
        dataCliente={
            'nombre':request.user.first_name,
            'apellidos':request.user.last_name,
            'email':request.user.email
        }

    frmCliente = ClienteForm(dataCliente)
    context = {
        'frmCliente':frmCliente
    }


    return render(request,"cuenta.html",context)\

def actualizarCliente(request):

    menseje = ""

    if request.method == "POST":
        frmCliente = ClienteForm(request.POST)
        if frmCliente.is_valid():
            dataCliente = frmCliente.cleaned_data #prepara los datos para ser insertados

            #actualizar usuario "tabla user"
            actUsuario = User.objects.get(pk=request.user.id)
            actUsuario.first_name = dataCliente["nombre"]
            actUsuario.last_name = dataCliente["apellidos"]
            actUsuario.email = dataCliente["email"]
            actUsuario.save()

            #registrar cliente "tabla cliente, la cual creamos"
            nuevoCliente = Cliente()
            nuevoCliente.usuario = actUsuario
            nuevoCliente.dni = dataCliente["dni"]
            nuevoCliente.direccion = dataCliente["direccion"]
            nuevoCliente.telefono = dataCliente["telefono"]
            nuevoCliente.sexo = dataCliente["sexo"]
            nuevoCliente.fecha_nacimiento = dataCliente["fecha_nacimiento"]
            nuevoCliente.save()

            mensaje = "Datos actualizados"

            context = {
                'menseje':mensaje,
                'frmCliente':frmCliente
            }

    return render(request,"cuenta.html", context)

"""VISTAS PARA PROCESO DE COMPRA"""
@login_required(login_url='/login')
def registrarPedido(request):
    
    try:
        clienteEditar = Cliente.objects.get(usuario = request.user)

        dataCliente = {
            'nombre':request.user.first_name,
            'apellidos':request.user.last_name,
            'email':request.user.email,
            'direccion':clienteEditar.direccion,
            'telefono':clienteEditar.telefono,
            'dni':clienteEditar.dni,
            'sexo':clienteEditar.sexo,
            'fecha_nacimiento':clienteEditar.fecha_nacimiento
        }
    except:
        dataCliente={
            'nombre':request.user.first_name,
            'apellidos':request.user.last_name,
            'email':request.user.email
        }

    frmCliente = ClienteForm(dataCliente)
    context = {
        'frmCliente':frmCliente
    }

    return render(request,'pedido.html',context)

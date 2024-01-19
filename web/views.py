from django.shortcuts import render,get_object_or_404,redirect
from .models import Categoria,Producto,Cliente,Pedido,PedidoDetalle
from .carrito import Cart
from django.contrib.auth.models import User
from django.contrib.auth import login,logout,authenticate
from .forms import ClienteForm
from django.contrib.auth.decorators import login_required
from paypal.standard.forms import PayPalPaymentsForm
from django.urls import reverse
from django.core.mail import send_mail

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

"""VISTA PEDIDO"""
@login_required(login_url="/login")
def confirmarPedido(request):
    
    context = {}

    if request.method == "POST":
        #actualizamos al usuario
        actUsuario = User.objects.get(pk=request.user.id)
        actUsuario.first_name = request.POST['nombre']
        actUsuario.last_name = request.POST['apellidos']
        actUsuario.save()
        #registramos o actualizamos cliente
        try:
            clientePedido = Cliente.objects.get(usuario=request.user)
            clientePedido.telefono = request.POST['telefono']
            clientePedido.direccion = request.POST['direccion']
            clientePedido.save()
        except:
            clientePedido = Cliente()
            clientePedido.usuario = actUsuario
            clientePedido.telefono = request.POST['telefono']
            clientePedido.direccion = request.POST['direccion']
            clientePedido.save()
        #registramos nuevo pedido
        numPedido = ''
        montoTotal = float(request.session.get('cartMontoTotal'))
        nuevoPedido = Pedido()
        nuevoPedido.cliente = clientePedido
        nuevoPedido.save()

        #registrar detalle de pedido
        carritoPedido = request.session.get('cart')
        for key,value in carritoPedido.items():
            productoPedido = Producto.objects.get(pk=value['producto_id'])
            detalle = PedidoDetalle()
            detalle.pedido = nuevoPedido
            detalle.producto = productoPedido
            detalle.cantidad = int(value['cantidad'])
            detalle.subtotal = float(value['subtotal'])
            detalle.save()

        #actualizar pedido
        numPedido = 'PED' + nuevoPedido.fecha_registro.strftime('%Y') + str(nuevoPedido.id)
        nuevoPedido.num_pedido = numPedido
        nuevoPedido.monto_total = montoTotal
        nuevoPedido.save()

        #registrar variable de sesion para el pedido
        request.session['pedidoID'] = nuevoPedido.id

        #Creamos boton de paypal
        paypal_dict = {
        "business": "sb-zc33y29302976@business.example.com",
        "amount": montoTotal,
        "item_name": "PEDIDO CÓDIGO" + numPedido,
        "invoice": numPedido,
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return": request.build_absolute_uri('/gracias'),
        "cancel_return": request.build_absolute_uri('/'),
        "custom": "premium_plan",  # Custom command to correlate to some function later (optional)
    }

        # Create the instance.
        formPaypal = PayPalPaymentsForm(initial=paypal_dict)

        context = {
            'pedido':nuevoPedido,
            'formPaypal':formPaypal
        }

        #limpiamos carrito
        carrito = Cart(request)
        carrito.clear()
    
    return render(request,"compra.html", context)


#prueba paypal
def view_that_asks_for_money(request):

    # What you want the button to do.
    paypal_dict = {
        "business": "sb-zc33y29302976@business.example.com",
        "amount": "100.00",
        "item_name": "producto prueba",
        "invoice": "100",
        "notify_url": request.build_absolute_uri(reverse('paypal-ipn')),
        "return": request.build_absolute_uri('/'),
        "cancel_return": request.build_absolute_uri('logoutUsuario'),
        "custom": "premium_plan",  # Custom command to correlate to some function later (optional)
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}

    
    return render(request, "payments.html", context)

"""VISTA GRACIAS PARA CUANDO SE CONFIRME LA COMPRA"""
@login_required(login_url='/login')
def gracias(request):
    paypalID = request.GET.get('PayerID', None)
    context = {}
    if paypalID is not None:
        pedidoID = request.session.get('pedidoID')
        pedido = Pedido.objects.get(pk=pedidoID)
        pedido.estado = '1'
        pedido.save() 

        send_mail(
            "Gracias por tu compra",
            "Tu número de pedido es: " + str(pedido.num_pedido),
            "elsolis800@gmail.com",
            [request.user.email],
            fail_silently=False,
        )

        context = {
            'pedido':pedido
        }
    else:
        return redirect('/')
    return render(request,"gracias.html")
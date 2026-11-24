import streamlit as st
import re
import json
import urllib.request
from datetime import datetime

# Configuración de la página web
st.set_page_config(
    page_title="Agente IA - Asistente de Ventas y Soporte",
    page_icon="🤖",
    layout="wide"
)

# -------------------------------------------------------------------------
# 1. BASE DE CONOCIMIENTO Y HERRAMIENTAS DEL AGENTE (ARQUITECTURA SAS)
# -------------------------------------------------------------------------
CATALOGO = {
    "laptop": {
        "nombre": "Portátil Lenovo IdeaPad 5 (Ryzen 7, 16GB RAM, 512GB SSD)",
        "precio": 2650000,
        "stock": 8,
        "categoria": "Computadores",
        "uso": "Ideal para programación, ingeniería, estudio universitario y multitarea."
    },
    "monitor": {
        "nombre": "Monitor LG UltraGear 24'' Full HD 144Hz IPS",
        "precio": 780000,
        "stock": 12,
        "categoria": "Pantallas",
        "uso": "Recomendado para diseño, programación con doble pantalla y videojuegos."
    },
    "teclado": {
        "nombre": "Teclado Mecánico Redragon Kumara RGB Switch Red",
        "precio": 210000,
        "stock": 15,
        "categoria": "Periféricos",
        "uso": "Escritura rápida y cómoda para jornadas largas de código u oficina."
    },
    "mouse": {
        "nombre": "Mouse Inalámbrico Logitech G305 Lightspeed",
        "precio": 195000,
        "stock": 20,
        "categoria": "Periféricos",
        "uso": "Alta precisión y batería de larga duración sin cables."
    },
    "audifonos": {
        "nombre": "Diadema HyperX Cloud Stinger 2 con Micrófono",
        "precio": 240000,
        "stock": 10,
        "categoria": "Audio",
        "uso": "Clases virtuales, reuniones y cancelación pasiva de ruido."
    }
}

# -------------------------------------------------------------------------
# 2. MEMORIA DEL AGENTE (ESTADO DE LA SESIÓN)
# -------------------------------------------------------------------------
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {
            "rol": "assistant",
            "contenido": (
                "Hola, soy tu **Agente Autónomo de Ventas y Atención al Cliente**.

"
                "Puedo atender tus solicitudes y ejecutar tareas en la tienda:
"
                "- **Asesoría de compra:** Dime tu presupuesto o qué necesitas (ej. *'Busco un portátil para programar'*).
"
                "- **Gestión del carrito:** Pídeme agregar productos (ej. *'Agregar laptop al carrito'*).
"
                "- **Rastreo de pedidos:** Consulta el estado de una orden (ej. *'Estado del pedido ORD-101'*).

"
                "¿Qué solicitud deseas realizar hoy?"
            )
        }
    ]

if "carrito" not in st.session_state:
    st.session_state.carrito = []

if "pedidos" not in st.session_state:
    st.session_state.pedidos = [
        {"Orden": "ORD-101", "Cliente": "Laura Gómez", "Total": "$2.860.000 COP", "Estado": "En camino"},
        {"Orden": "ORD-102", "Cliente": "Andrés Ríos", "Total": "$975.000 COP", "Estado": "Entregado"}
    ]


# -------------------------------------------------------------------------
# 3. MOTOR DE RAZONAMIENTO Y EJECUCIÓN DE TAREAS DEL AGENTE
# -------------------------------------------------------------------------
def agregar_producto_carrito(clave_producto: str):
    item = CATALOGO[clave_producto]
    st.session_state.carrito.append({
        "clave": clave_producto,
        "nombre": item["nombre"],
        "precio": item["precio"]
    })


def procesar_solicitud_agente(instruccion: str, api_key: str = "") -> str:
    texto = instruccion.strip()
    texto_min = texto.lower()

    # Opción A: Conexión con modelo LLM externo si el usuario proporciona API Key
    if api_key.strip():
        try:
            url = "https://api.openai.com/v1/chat/completions"
            resumen_catalogo = "
".join(
                [f"- {v['nombre']}: ${v['precio']:,} COP (Stock: {v['stock']})" for v in CATALOGO.values()]
            )
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Eres un Agente Autónomo de Ventas y Atención al Cliente de una tienda de tecnología en Colombia. "
                            "Catálogo disponible:
" + resumen_catalogo +
                            "
Políticas: envíos gratis por compras mayores a $500.000 COP, garantía de 12 meses, "
                            "cupón de descuento TECH10 para 10% menos. Responde de forma clara y directa."
                        )
                    },
                    {"role": "user", "content": texto}
                ],
                "temperature": 0.4
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key.strip()}"
                }
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"No se pudo conectar con la API externa ({e}). Respondiendo con el motor autónomo local:

" + procesar_solicitud_agente(instruccion, "")

    # Opción B: Motor autónomo local (Percepción -> Decisión -> Ejecución de tarea)

    # Tarea 1: Agregar un producto al carrito por instrucción directa
    if any(verbo in texto_min for verbo in ["agregar", "añadir", "comprar", "meter al carrito"]):
        for clave, datos in CATALOGO.items():
            if clave in texto_min or ("portatil" in texto_min and clave == "laptop") or ("portátil" in texto_min and clave == "laptop"):
                agregar_producto_carrito(clave)
                return (
                    f"**Tarea ejecutada:** Agregué **{datos['nombre']}** (${datos['precio']:,} COP) a tu carrito de compras.

"
                    "Revisa el panel izquierdo para ver el total actualizado o descargar tu cotización."
                )
        return "Indícame qué producto deseas agregar al carrito: **laptop**, **monitor**, **teclado**, **mouse** o **audifonos**."

    # Tarea 2: Rastrear estado de un pedido existente
    match_orden = re.search(r"ord-\d+", texto_min)
    if match_orden or any(p in texto_min for p in ["pedido", "orden", "rastrear", "envio", "envío"]):
        if match_orden:
            codigo = match_orden.group(0).upper()
            for p in st.session_state.pedidos:
                if p["Orden"] == codigo:
                    return (
                        f"**Consulta de orden {codigo}:**
"
                        f"- **Cliente:** {p['Cliente']}
"
                        f"- **Valor:** {p['Total']}
"
                        f"- **Estado actual:** {p['Estado']}"
                    )
            return f"No encontré ninguna orden con el código **{codigo}**. Verifica el número en la pestaña **Seguimiento de Pedidos**."
        return "Para rastrear tu compra, escribe el código de tu orden (por ejemplo: *'Estado del pedido ORD-101'*)."

    # Tarea 3: Recomendación según presupuesto o necesidad
    numeros = [int(n.replace(".", "").replace(",", "")) for n in re.findall(r"\d[\d\.,]*", texto_min)]
    if numeros and any(p in texto_min for p in ["presupuesto", "tengo", "pesos", "cop", "alcanza", "barato", "economico", "económico"]):
        presupuesto = max(numeros)
        opciones = [v for v in CATALOGO.values() if v["precio"] <= presupuesto]
        if not opciones:
            return f"Con un presupuesto de **${presupuesto:,} COP** aún no cubres el artículo más económico ($195.000 COP). Te sugiero revisar nuestros periféricos."
        lista_txt = "
".join([f"- **{o['nombre']}**: ${o['precio']:,} COP ({o['uso']})" for o in opciones])
        return f"Con un presupuesto de **${presupuesto:,} COP** puedes adquirir cualquiera de estas opciones disponibles:

{lista_txt}"

    # Tarea 4: Mostrar catálogo y precios
    if any(p in texto_min for p in ["catalogo", "catálogo", "productos", "precio", "precios", "tienen", "venden", "recomienda"]):
        lista_completa = "
".join(
            [f"- **{v['nombre']}** | ${v['precio']:,} COP | Disponibles: {v['stock']} unid." for v in CATALOGO.values()]
        )
        return (
            "**Catálogo disponible en tienda:**

"
            f"{lista_completa}

"
            "Si quieres añadir alguno, escribe por ejemplo: *'Agregar teclado al carrito'*."
        )

    # Tarea 5: Políticas de garantía, envíos y descuentos
    if any(p in texto_min for p in ["garantia", "garantía", "descuento", "cupon", "cupón", "pago", "devolucion", "devolución"]):
        return (
            "**Información de atención al cliente:**
"
            "- **Garantía:** 12 meses directos por defectos de fábrica en todos los equipos.
"
            "- **Envíos:** Gratis a nivel nacional en compras superiores a $500.000 COP.
"
            "- **Descuento activo:** Usa el código **TECH10** en el carrito lateral para obtener un 10% de descuento."
        )

    # Saludo inicial
    if any(p in texto_min for p in ["hola", "buenos dias", "buenas tardes", "buenas noches", "ayuda"]):
        return (
            "Hola. Soy el agente virtual de ventas y soporte. Puedes preguntarme por el **catálogo de productos**, "
            "pedirme que **agregue un equipo al carrito**, consultar **garantías** o rastrear un pedido como **ORD-101**."
        )

    # Respuesta guía por defecto
    return (
        "No identifiqué una acción exacta en tu mensaje. Prueba con alguna de estas instrucciones:
"
        "- *'Muéstrame el catálogo y precios'*
"
        "- *'Agregar monitor al carrito'*
"
        "- *'Tengo un presupuesto de 800000 pesos'*
"
        "- *'Estado del pedido ORD-101'*"
    )


# -------------------------------------------------------------------------
# 4. INTERFAZ GRÁFICA WEB (STREAMLIT)
# -------------------------------------------------------------------------

# Barra lateral: Funcionalidad adicional (Carrito de compras y cotizador)
with st.sidebar:
    st.header("🛒 Carrito y Cotizador")
    st.caption("Funcionalidad adicional vinculada al agente de ventas.")

    producto_manual = st.selectbox(
        "Seleccionar producto",
        options=list(CATALOGO.keys()),
        format_func=lambda k: f"{CATALOGO[k]['nombre'].split('(')[0].strip()} (${CATALOGO[k]['precio']:,})"
    )

    col_add, col_clear = st.columns(2)
    if col_add.button("➕ Añadir", use_container_width=True):
        agregar_producto_carrito(producto_manual)
        st.rerun()

    if col_clear.button("🗑️ Vaciar", use_container_width=True):
        st.session_state.carrito = []
        st.rerun()

    st.divider()

    if len(st.session_state.carrito) == 0:
        st.info("Tu carrito está vacío. Pídele al agente que agregue un producto o añádelo arriba.")
    else:
        subtotal = sum(item["precio"] for item in st.session_state.carrito)
        for idx, item in enumerate(st.session_state.carrito, start=1):
            st.write(f"{idx}. {item['nombre'].split('(')[0].strip()} - **${item['precio']:,}**")

        cupon = st.text_input("Cupón de descuento", placeholder="Escribe TECH10")
        descuento = round(subtotal * 0.10) if cupon.strip().upper() == "TECH10" else 0
        total_final = subtotal - descuento

        st.write(f"**Subtotal:** ${subtotal:,} COP")
        if descuento > 0:
            st.write(f"**Descuento (10%):** -${descuento:,} COP")
        st.subheader(f"Total: ${total_final:,} COP")

        # Descarga de cotización generada
        texto_cotizacion = (
            f"COTIZACIÓN OFICIAL - AGENTE DE VENTAS
"
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"
            f"----------------------------------------
"
            + "
".join([f"- {i['nombre']}: ${i['precio']:,} COP" for i in st.session_state.carrito])
            + f"
----------------------------------------
"
            f"Subtotal: ${subtotal:,} COP
"
            f"Descuento: ${descuento:,} COP
"
            f"TOTAL A PAGAR: ${total_final:,} COP
"
        )
        st.download_button(
            label="📄 Descargar Cotización",
            data=texto_cotizacion,
            file_name="cotizacion_agente.txt",
            mime="text/plain",
            use_container_width=True
        )

    st.divider()
    with st.expander("🔑 Conectar Modelo LLM (Opcional)"):
        openai_api_key = st.text_input(
            "API Key de OpenAI",
            type="password",
            help="Opcional. Si se deja vacío, el agente ejecuta su motor autónomo local."
        )


# Área principal
st.title("🤖 Agente Autónomo de Ventas y Atención al Cliente")
st.caption("Sistema de IA conversacional con ejecución de tareas, cotización en tiempo real y seguimiento de órdenes.")

pestana_chat, pestana_pedidos, pestana_catalogo = st.tabs([
    "💬 Chat con el Agente",
    "📦 Seguimiento de Pedidos",
    "📋 Catálogo Disponible"
])

# Pestaña 1: Interacción con el agente
with pestana_chat:
    b1, b2, b3 = st.columns(3)
    accion_rapida = None
    if b1.button("📋 Ver catálogo y precios", use_container_width=True):
        accion_rapida = "Muéstrame el catálogo y precios"
    if b2.button("🛒 Agregar laptop al carrito", use_container_width=True):
        accion_rapida = "Agregar laptop al carrito"
    if b3.button("📦 Rastrear orden ORD-101", use_container_width=True):
        accion_rapida = "Estado del pedido ORD-101"

    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["rol"]):
            st.markdown(mensaje["contenido"])

    entrada_chat = st.chat_input("Escribe tu pregunta o instrucción para el agente...")
    solicitud = accion_rapida or entrada_chat

    if solicitud:
        st.session_state.mensajes.append({"rol": "user", "contenido": solicitud})
        with st.chat_message("user"):
            st.markdown(solicitud)

        respuesta_agente = procesar_solicitud_agente(solicitud, openai_api_key)
        st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta_agente})
        with st.chat_message("assistant"):
            st.markdown(respuesta_agente)

        if accion_rapida:
            st.rerun()

# Pestaña 2: Registro y consulta de pedidos
with pestana_pedidos:
    st.subheader("Órdenes Registradas")
    st.dataframe(st.session_state.pedidos, use_container_width=True)

    st.markdown("**Generar nueva orden desde el carrito actual**")
    nombre_comprador = st.text_input("Nombre del cliente para la orden", placeholder="Ej. Sofía Martínez")
    if st.button("Confirmar Pedido"):
        if len(st.session_state.carrito) == 0:
            st.warning("Agrega al menos un producto al carrito antes de confirmar el pedido.")
        elif not nombre_comprador.strip():
            st.warning("Escribe el nombre del cliente.")
        else:
            nuevo_codigo = f"ORD-{101 + len(st.session_state.pedidos)}"
            total_orden = sum(i["precio"] for i in st.session_state.carrito)
            st.session_state.pedidos.append({
                "Orden": nuevo_codigo,
                "Cliente": nombre_comprador.strip(),
                "Total": f"${total_orden:,} COP",
                "Estado": "Procesando envío"
            })
            st.session_state.carrito = []
            st.success(f"Orden **{nuevo_codigo}** creada con éxito. Ahora puedes consultarla en el chat del agente.")
            st.rerun()

# Pestaña 3: Tabla de inventario
with pestana_catalogo:
    st.subheader("Inventario de Productos")
    filas_catalogo = [
        {
            "Clave": k,
            "Producto": v["nombre"],
            "Categoría": v["categoria"],
            "Precio (COP)": f"${v['precio']:,}",
            "Stock": v["stock"],
            "Recomendación": v["uso"]
        }
        for k, v in CATALOGO.items()
    ]
    st.dataframe(filas_catalogo, use_container_width=True)

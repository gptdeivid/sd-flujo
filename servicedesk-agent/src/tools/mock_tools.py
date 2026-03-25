"""Mock tools for MVP development and testing."""

from langchain_core.tools import tool


# === IT Support Tools ===


@tool
def check_system_status(system_name: str) -> str:
    """Check the status of a specific system.

    Args:
        system_name: Name of the system to check (email, vpn, erp, crm, etc.)

    Returns:
        Current status of the system.
    """
    # MVP: Simulated response
    systems = {
        "email": "Sistema de email operativo. Último incidente hace 5 días.",
        "vpn": "VPN operativa. Latencia promedio: 45ms.",
        "erp": "ERP operativo. Próximo mantenimiento programado: domingo 3am.",
        "crm": "CRM operativo. Versión actual: 4.2.1",
        "red": "Red corporativa operativa. Uso actual: 65%.",
    }

    system_lower = system_name.lower()
    for key, value in systems.items():
        if key in system_lower:
            return value

    return f"Sistema '{system_name}' no encontrado en el monitoreo. Contacte a infraestructura."


@tool
def get_troubleshooting_guide(issue_type: str) -> str:
    """Get troubleshooting guide for a specific issue type.

    Args:
        issue_type: Type of issue (network, software, hardware, access, vpn)

    Returns:
        Recommended troubleshooting steps.
    """
    guides = {
        "network": """GUÍA DE RED:
1. Verificar cable de red o conexión WiFi
2. Reiniciar el router/switch si es posible
3. Ejecutar 'ipconfig /release' y 'ipconfig /renew'
4. Verificar configuración de proxy
5. Si persiste, contactar a Infraestructura""",
        "software": """GUÍA DE SOFTWARE:
1. Reiniciar la aplicación
2. Limpiar caché y archivos temporales
3. Verificar actualizaciones pendientes
4. Reinstalar si es necesario
5. Verificar compatibilidad con el sistema""",
        "hardware": """GUÍA DE HARDWARE:
1. Verificar todas las conexiones físicas
2. Reiniciar el equipo completamente
3. Probar en otro puerto USB/conexión
4. Verificar drivers actualizados
5. Reportar para revisión física si persiste""",
        "access": """GUÍA DE ACCESOS:
1. Verificar usuario y contraseña
2. Intentar reset de contraseña en el portal
3. Verificar que la cuenta no esté bloqueada
4. Contactar al supervisor para verificar permisos
5. Crear ticket de acceso si es nuevo permiso""",
        "vpn": """GUÍA DE VPN:
1. Verificar conexión a internet estable
2. Reiniciar cliente VPN
3. Verificar credenciales de VPN
4. Probar servidor VPN alternativo
5. Verificar firewall local no bloquee""",
    }

    issue_lower = issue_type.lower()
    for key, value in guides.items():
        if key in issue_lower:
            return value

    return "Consulte con el equipo de IT para soporte personalizado sobre este tipo de problema."


@tool
def create_it_ticket(
    title: str,
    description: str,
    priority: str = "medium",
) -> str:
    """Create an IT support ticket (simulated).

    Args:
        title: Brief ticket title.
        description: Detailed description of the issue.
        priority: Ticket priority (low, medium, high, critical).

    Returns:
        Confirmation with ticket ID.
    """
    # MVP: Simulated ticket creation
    import random

    ticket_id = f"IT-{random.randint(10000, 99999)}"
    return f"""Ticket creado exitosamente:
- ID: {ticket_id}
- Título: {title}
- Prioridad: {priority}
- Estado: Abierto
- SLA estimado: {'4 horas' if priority == 'high' else '24 horas'}

Un técnico revisará su caso pronto."""


# === Billing Tools ===


@tool
def lookup_invoice(invoice_id: str) -> str:
    """Look up invoice information.

    Args:
        invoice_id: Invoice ID or number.

    Returns:
        Invoice details.
    """
    # MVP: Simulated response
    return f"""Factura {invoice_id}:
- Monto: $1,500.00 MXN
- Fecha de emisión: 2026-03-15
- Fecha de vencimiento: 2026-04-15
- Estado: Pagada
- Método de pago: Transferencia bancaria
- Referencia: REF-{invoice_id[-4:]}"""


@tool
def check_payment_status(reference: str) -> str:
    """Check payment status.

    Args:
        reference: Payment reference or transaction number.

    Returns:
        Payment status.
    """
    # MVP: Simulated response
    return f"""Pago con referencia {reference}:
- Estado: Confirmado
- Fecha de aplicación: 2026-03-20
- Monto: $1,500.00 MXN
- Aplicado a: Factura más antigua pendiente
- Método: Transferencia bancaria"""


@tool
def request_invoice_copy(invoice_id: str, email: str) -> str:
    """Request a copy of an invoice.

    Args:
        invoice_id: Invoice ID to request copy.
        email: Email to send the copy.

    Returns:
        Confirmation of request.
    """
    return f"""Solicitud registrada:
- Factura: {invoice_id}
- Se enviará a: {email}
- Tiempo estimado: 15-30 minutos

Recibirá la copia en formato PDF."""


# === General Inquiry Tools ===


@tool
def search_faq(query: str) -> str:
    """Search in the FAQ knowledge base.

    Args:
        query: Search term or question.

    Returns:
        Relevant FAQ found.
    """
    faqs = {
        "horario": """HORARIOS DE ATENCIÓN:
- Service Desk: Lunes a Viernes 8:00-18:00
- Soporte de emergencia: 24/7 (solo críticos)
- Facturación: Lunes a Viernes 9:00-17:00""",
        "contacto": """INFORMACIÓN DE CONTACTO:
- Email: soporte@empresa.com
- Teléfono: +52 55 1234 5678
- Chat: portal.empresa.com/chat
- Emergencias: +52 55 1234 5679""",
        "password": """RESET DE CONTRASEÑA:
1. Visite: portal.empresa.com/reset
2. Ingrese su email corporativo
3. Recibirá un enlace de recuperación
4. El enlace expira en 24 horas""",
        "vpn": """CONFIGURACIÓN DE VPN:
1. Descargue el cliente desde: portal.empresa.com/vpn
2. Use sus credenciales corporativas
3. Servidor: vpn.empresa.com
4. Soporte: soporte@empresa.com""",
        "ticket": """SEGUIMIENTO DE TICKETS:
1. Visite: portal.empresa.com/tickets
2. Inicie sesión con credenciales corporativas
3. Verá todos sus tickets abiertos y cerrados
4. Puede agregar comentarios a tickets abiertos""",
    }

    query_lower = query.lower()
    for key, value in faqs.items():
        if key in query_lower:
            return value

    return "No se encontró información específica. Un agente le ayudará con su consulta."


@tool
def get_office_info(office_name: str = "principal") -> str:
    """Get office information.

    Args:
        office_name: Office name or location (principal, norte, sur).

    Returns:
        Office information.
    """
    offices = {
        "principal": """OFICINA PRINCIPAL:
- Dirección: Av. Reforma 123, Col. Centro, CDMX
- Teléfono: +52 55 1234 5678
- Horario: Lunes a Viernes 8:00-18:00
- Estacionamiento disponible""",
        "norte": """OFICINA NORTE:
- Dirección: Blvd. Industrial 456, Monterrey, NL
- Teléfono: +52 81 8765 4321
- Horario: Lunes a Viernes 8:00-18:00""",
        "sur": """OFICINA SUR:
- Dirección: Calle Principal 789, Mérida, Yuc
- Teléfono: +52 99 9876 5432
- Horario: Lunes a Viernes 9:00-17:00""",
    }

    office_lower = office_name.lower()
    for key, value in offices.items():
        if key in office_lower:
            return value

    return offices["principal"]

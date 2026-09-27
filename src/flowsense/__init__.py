"""Flowsense — práctica de ingeniería de Python.

Este __init__ define la API pública del paquete. Lo que no se exporte
aquí se considera interno y puede cambiar sin previo aviso.
"""

from flowsense.types_practice import (
    Invoice,
    Printable,
    Receipt,
    Status,
    build_invoice,
    chunk,
    count_by_vendor,
    describe_invoice,
    find_invoice,
    first,
    next_status,
    print_all,
    set_status,
)

__version__ = "0.1.0"

# __all__ declara qué se exporta con "from flowsense import *".
# Más importante: es documentación ejecutable de tu superficie pública,
# y ruff la usa para no marcar estos imports como "no usados".
__all__ = [
    "Invoice",
    "Printable",
    "Receipt",
    "Status",
    "__version__",
    "build_invoice",
    "chunk",
    "count_by_vendor",
    "describe_invoice",
    "find_invoice",
    "first",
    "next_status",
    "print_all",
    "set_status",
]

"""Práctica de tipado — los seis puntos de la sesión 3.

Correr:  uv run mypy .   →  debe decir "Success: no issues found"
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, NotRequired, Protocol, TypedDict, TypeVar, Unpack

# ══════════════════════════════════════════════════════════════════════
# PUNTO 5 — Protocol + Invoice
# Va primero porque los puntos 2 y 6 usan la clase Invoice, y Python
# ejecuta el módulo de arriba hacia abajo: una clase debe existir antes
# de que otro código la instancie.
# ══════════════════════════════════════════════════════════════════════


class Printable(Protocol):
    """Contrato: cualquier objeto con render() -> str lo cumple.

    No hay que heredar de Printable. Mypy compara la FORMA de la clase
    contra este protocolo. A eso se le llama tipado estructural.
    """

    def render(self) -> str: ...


class Invoice:
    """Cumple Printable sin heredarlo ni mencionarlo."""

    def __init__(self, number: str, vendor: str, total: Decimal) -> None:
        self.number = number
        self.vendor = vendor
        self.total = total

    def render(self) -> str:
        return f"{self.number} | {self.vendor} | ${self.total:,.2f}"


class Receipt:
    """Otra clase, sin relación con Invoice, que también cumple Printable."""

    def __init__(self, folio: str) -> None:
        self.folio = folio

    def render(self) -> str:
        return f"Receipt {self.folio}"


def print_all(items: list[Printable]) -> list[str]:
    """Acepta Invoice, Receipt o cualquier cosa con render() -> str."""
    return [item.render() for item in items]


# ══════════════════════════════════════════════════════════════════════
# PUNTO 1 — list[str] -> dict[str, int]
# ══════════════════════════════════════════════════════════════════════


def count_by_vendor(invoice_numbers: list[str]) -> dict[str, int]:
    """Cuenta facturas por proveedor a partir del prefijo del folio.

    ["ACME-001", "ACME-002", "GLOBEX-001"] -> {"ACME": 2, "GLOBEX": 1}
    """
    counts: dict[str, int] = {}  # la anotación es obligatoria en strict:
    # de un {} vacío mypy no puede deducir nada
    for number in invoice_numbers:
        vendor = number.split("-")[0]  # split siempre devuelve al menos 1 elemento
        counts[vendor] = counts.get(vendor, 0) + 1
    return counts


# ══════════════════════════════════════════════════════════════════════
# PUNTO 2 — una función que devuelve X | None, y otra que la consume
# ══════════════════════════════════════════════════════════════════════

_CATALOG: dict[str, Invoice] = {
    "ACME-001": Invoice("ACME-001", "Acme Industrial", Decimal("632.20")),
    "GLOBEX-001": Invoice("GLOBEX-001", "Globex", Decimal("1450.00")),
}


def find_invoice(number: str) -> Invoice | None:
    """Devuelve la factura o None. El tipo de retorno DECLARA que puede fallar."""
    return _CATALOG.get(number)  # .get() devuelve None si no existe


def describe_invoice(number: str) -> str:
    """Consume find_invoice y maneja el None explícitamente."""
    invoice = find_invoice(number)

    if invoice is None:  # sin esta guarda, mypy marca error
        return f"Invoice {number} not found"

    # A partir de aquí mypy YA SABE que invoice es Invoice, no None.
    # A eso se le llama "narrowing": la guarda estrechó el tipo.
    return invoice.render()


# ══════════════════════════════════════════════════════════════════════
# PUNTO 3 — Literal: solo tres valores permitidos
# ══════════════════════════════════════════════════════════════════════

Status = Literal["pending", "approved", "rejected"]


def set_status(invoice_id: str, status: Status) -> str:
    """Solo acepta los tres literales. Cualquier otro string es error de mypy."""
    return f"{invoice_id} -> {status}"


def next_status(current: Status, approved: bool) -> Status:
    """Transición de estado. Solo 'pending' puede cambiar."""
    if current != "pending":
        return current  # mypy sabe: aquí current es
        # Literal["approved", "rejected"]
    return "approved" if approved else "rejected"


# ══════════════════════════════════════════════════════════════════════
# PUNTO 4 — TypeVar: genérica sobre cualquier tipo
# ══════════════════════════════════════════════════════════════════════

T = TypeVar("T")


def first(items: list[T]) -> T | None:
    """Primer elemento, o None si está vacía.

    T conserva el tipo: first([1,2]) es int|None, first(["a"]) es str|None.
    Sin TypeVar tendrías que devolver Any y perderías toda la verificación.
    """
    return items[0] if items else None


def chunk(items: list[T], size: int) -> list[list[T]]:
    """Parte una lista en bloques. El tipo de los elementos se conserva."""
    if size < 1:
        raise ValueError("size must be >= 1")
    return [items[i : i + size] for i in range(0, len(items), size)]


# ══════════════════════════════════════════════════════════════════════
# PUNTO 6 — TypedDict + Unpack: **kwargs tipados
# ══════════════════════════════════════════════════════════════════════


class InvoiceFields(TypedDict):
    """Declara las llaves y el tipo de cada valor.

    NotRequired marca las opcionales: las demás son obligatorias.
    """

    number: str
    vendor: str
    total: Decimal
    purchase_order: NotRequired[str | None]


def build_invoice(**fields: Unpack[InvoiceFields]) -> Invoice:
    """**kwargs tipados.

    Unpack le dice a mypy: "los kwargs de esta función son exactamente
    las llaves de InvoiceFields". Así verifica nombres Y tipos de cada
    argumento con nombre, cosa que **kwargs: Any nunca haría.
    """
    po = fields.get("purchase_order")  # NotRequired -> hay que usar .get()
    invoice = Invoice(
        number=fields["number"],  # obligatoria: acceso directo es seguro
        vendor=fields["vendor"],
        total=fields["total"],
    )
    if po is not None:
        print(f"linked to {po}")
    return invoice


# ══════════════════════════════════════════════════════════════════════
# Demostración
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(count_by_vendor(["ACME-001", "ACME-002", "GLOBEX-001"]))
    print(describe_invoice("ACME-001"))
    print(describe_invoice("NOPE-999"))
    print(set_status("ACME-001", "approved"))
    print(next_status("pending", approved=False))
    print(first([1, 2, 3]), first([]))
    print(chunk(["a", "b", "c", "d", "e"], 2))
    print(print_all([Invoice("A-1", "Acme", Decimal("10")), Receipt("R-9")]))
    print(build_invoice(number="A-2", vendor="Acme", total=Decimal("99.50")).render())

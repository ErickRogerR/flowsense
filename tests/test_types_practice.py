"""Tests de los seis puntos de tipado de la sesión 3.

Correr:  uv run pytest
Verboso: uv run pytest -v
Uno solo: uv run pytest -k "narrowing"
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from flowsense import (
    Invoice,
    Printable,
    Receipt,
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

# Importamos desde `flowsense`, no desde `flowsense.types_practice`.
# Eso prueba la API pública — lo mismo que usaría un cliente — y de paso
# verifica que el __init__.py exporta lo que dice exportar.


# ══════════════════════════════════════════════════════════════════════
# FIXTURES — datos de prueba reutilizables
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_invoice() -> Invoice:
    """Una factura válida.

    Una fixture es una función que prepara datos y se inyecta en los tests
    que la pidan por nombre en sus parámetros. Pytest la ejecuta DE NUEVO
    para cada test, así que un test que mute el objeto no puede contaminar
    al siguiente.
    """
    return Invoice("ACME-001", "Acme Industrial", Decimal("632.20"))


@pytest.fixture
def invoice_numbers() -> list[str]:
    return ["ACME-001", "ACME-002", "GLOBEX-001", "ACME-003"]


# ══════════════════════════════════════════════════════════════════════
# PUNTO 1 — count_by_vendor
# ══════════════════════════════════════════════════════════════════════


class TestCountByVendor:
    """Agrupar en clase es solo organización: sin herencia, sin setUp."""

    def test_counts_invoices_per_vendor(self, invoice_numbers: list[str]) -> None:
        assert count_by_vendor(invoice_numbers) == {"ACME": 3, "GLOBEX": 1}

    def test_empty_list_returns_empty_dict(self) -> None:
        # El caso borde que nunca aparece en pruebas manuales y siempre
        # aparece en producción: la lista vacía.
        assert count_by_vendor([]) == {}

    def test_single_invoice(self) -> None:
        assert count_by_vendor(["ACME-001"]) == {"ACME": 1}

    def test_number_without_separator_uses_whole_string(self) -> None:
        # Documenta el comportamiento real ante entrada malformada.
        # Un test así vale doble: verifica Y deja escrito qué se decidió.
        assert count_by_vendor(["ACME"]) == {"ACME": 1}

    def test_case_sensitivity_is_not_normalised(self) -> None:
        # Este test documenta una LIMITACIÓN conocida, no un acierto.
        # Si algún día decides normalizar, este test falla y te avisa
        # que estás cambiando comportamiento existente.
        assert count_by_vendor(["acme-001", "ACME-002"]) == {"acme": 1, "ACME": 1}


# ══════════════════════════════════════════════════════════════════════
# PUNTO 2 — find_invoice / describe_invoice y el narrowing
# ══════════════════════════════════════════════════════════════════════


class TestFindInvoice:
    def test_returns_invoice_when_it_exists(self) -> None:
        invoice = find_invoice("ACME-001")

        # La guarda no es solo para mypy: sin ella, el assert de abajo
        # fallaría con AttributeError en vez de con un mensaje claro.
        assert invoice is not None
        assert invoice.vendor == "Acme Industrial"

    def test_returns_none_when_missing(self) -> None:
        assert find_invoice("NOPE-999") is None

    def test_empty_string_returns_none(self) -> None:
        assert find_invoice("") is None


class TestDescribeInvoice:
    def test_renders_existing_invoice(self) -> None:
        result = describe_invoice("ACME-001")

        assert "ACME-001" in result
        assert "Acme Industrial" in result
        # No comparamos el string completo a propósito: eso amarraría el
        # test al formato exacto de render() y se rompería con cualquier
        # cambio cosmético. Verifica lo que importa, no todo.

    def test_handles_missing_invoice_without_raising(self) -> None:
        # ESTE es el test importante de la sección. Comprueba que el
        # camino del None está manejado, que es donde vive el
        # AttributeError: 'NoneType' de producción.
        result = describe_invoice("NOPE-999")

        assert "not found" in result.lower()


# ══════════════════════════════════════════════════════════════════════
# PUNTO 3 — Literal y transiciones de estado
# ══════════════════════════════════════════════════════════════════════


class TestStatus:
    def test_set_status_formats_output(self) -> None:
        assert set_status("ACME-001", "approved") == "ACME-001 -> approved"

    @pytest.mark.parametrize(
        ("current", "approved", "expected"),
        [
            ("pending", True, "approved"),
            ("pending", False, "rejected"),
            ("approved", True, "approved"),  # ya resuelta: no cambia
            ("approved", False, "approved"),  # ni siquiera con approved=False
            ("rejected", True, "rejected"),  # terminal
            ("rejected", False, "rejected"),
        ],
    )
    def test_next_status_transitions(self, current: str, approved: bool, expected: str) -> None:
        """parametrize genera SEIS tests independientes de una función.

        Si uno falla, pytest te dice exactamente cuál combinación
        (test_next_status_transitions[approved-False-approved]) en vez de
        un genérico "el test de estados falló". Es la diferencia entre
        cinco segundos y diez minutos de depuración.
        """
        assert next_status(current, approved=approved) == expected  # type: ignore[arg-type]
        # El type: ignore es necesario porque parametrize pasa str, no
        # Literal. Es una de las pocas veces donde el ignore está
        # justificado: el tipo real lo garantiza la tabla de arriba.


# ══════════════════════════════════════════════════════════════════════
# PUNTO 4 — TypeVar: first y chunk
# ══════════════════════════════════════════════════════════════════════


class TestFirst:
    def test_returns_first_element(self) -> None:
        assert first([10, 20, 30]) == 10

    def test_empty_list_returns_none_instead_of_raising(self) -> None:
        # Sin el "if items else None" esto sería IndexError.
        assert first([]) is None

    def test_preserves_element_type(self) -> None:
        # En ejecución esto es trivial; el valor real es que mypy sabe
        # que el resultado es str | None y no Any.
        assert first(["a", "b"]) == "a"

    def test_falsy_first_element_is_still_returned(self) -> None:
        # Caso borde real: si la implementación usara "if items[0]" en vez
        # de "if items", un 0 o un "" se tratarían como lista vacía.
        assert first([0, 1, 2]) == 0
        assert first([""]) == ""


class TestChunk:
    def test_splits_evenly(self) -> None:
        assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    def test_includes_the_remainder(self) -> None:
        # EL test que atrapa el bug más caro de esta función: el último
        # lote incompleto que se queda sin procesar. Cinco elementos en
        # lotes de dos son tres lotes, no dos.
        assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    def test_size_larger_than_list_returns_single_chunk(self) -> None:
        assert chunk([1, 2], 10) == [[1, 2]]

    def test_empty_list_returns_empty_list(self) -> None:
        assert chunk([], 3) == []

    @pytest.mark.parametrize("bad_size", [0, -1, -100])
    def test_invalid_size_raises_value_error(self, bad_size: int) -> None:
        """pytest.raises verifica que la excepción correcta se lance.

        El bloque falla si NO se lanza, o si se lanza otra distinta.
        El match comprueba el mensaje: un error correcto con mensaje
        inútil sigue siendo un problema a las 3 de la mañana.
        """
        with pytest.raises(ValueError, match="size must be >= 1"):
            chunk([1, 2, 3], bad_size)


# ══════════════════════════════════════════════════════════════════════
# PUNTO 5 — Protocol
# ══════════════════════════════════════════════════════════════════════


class TestPrintable:
    def test_invoice_renders(self, sample_invoice: Invoice) -> None:
        rendered = sample_invoice.render()

        assert "ACME-001" in rendered
        assert "632.20" in rendered

    def test_print_all_accepts_unrelated_classes(self, sample_invoice: Invoice) -> None:
        """La prueba del tipado estructural.

        Invoice y Receipt no comparten clase base ni se conocen entre sí.
        Las dos funcionan porque TIENEN render() -> str. Eso es lo que
        Protocol compra: acoplarse a una capacidad, no a una jerarquía.
        """
        items: list[Printable] = [sample_invoice, Receipt("R-900")]

        rendered = print_all(items)

        assert len(rendered) == 2
        assert "ACME-001" in rendered[0]
        assert "R-900" in rendered[1]

    def test_print_all_with_empty_list(self) -> None:
        assert print_all([]) == []

    def test_a_new_class_satisfies_the_protocol_without_inheriting(self) -> None:
        """Define una clase aquí mismo y comprueba que encaja."""

        class DebitNote:  # no hereda de nada
            def render(self) -> str:
                return "Debit note"

        assert print_all([DebitNote()]) == ["Debit note"]


# ══════════════════════════════════════════════════════════════════════
# PUNTO 6 — TypedDict + Unpack
# ══════════════════════════════════════════════════════════════════════


class TestBuildInvoice:
    def test_builds_with_required_fields_only(self) -> None:
        invoice = build_invoice(number="A-100", vendor="Acme", total=Decimal("250.00"))

        assert invoice.number == "A-100"
        assert invoice.vendor == "Acme"
        assert invoice.total == Decimal("250.00")

    def test_builds_with_optional_purchase_order(self) -> None:
        invoice = build_invoice(
            number="A-101",
            vendor="Acme",
            total=Decimal("250.00"),
            purchase_order="PO-004417",
        )

        assert invoice.number == "A-101"

    def test_optional_field_explicitly_none(self) -> None:
        invoice = build_invoice(
            number="A-102",
            vendor="Acme",
            total=Decimal("10.00"),
            purchase_order=None,
        )

        assert invoice.total == Decimal("10.00")

    def test_decimal_precision_is_preserved(self) -> None:
        """Decimal no pierde precisión; float sí.

        Este test existe para documentar POR QUÉ el campo es Decimal.
        Con float, 0.1 + 0.2 != 0.3 y una conciliación falla al azar.
        """
        invoice = build_invoice(
            number="A-103", vendor="Acme", total=Decimal("0.1") + Decimal("0.2")
        )

        assert invoice.total == Decimal("0.3")
        assert 0.1 + 0.2 != 0.3  # el mismo cálculo con float, para contraste

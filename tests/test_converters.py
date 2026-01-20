"""Testes para conversores de tipo."""

import pytest

from django_env_loader.exceptions import ValidationError
from django_env_loader.loader import TypeConverter


class TestBoolConverter:
    """Testes para conversão de valores booleanos."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("Yes", True),
            ("y", True),
            ("on", True),
            ("ON", True),
            ("t", True),
            ("sim", True),
            ("s", True),
            (True, True),
        ],
    )
    def test_true_values(self, value, expected):
        """Testa conversão de valores verdadeiros."""
        assert TypeConverter.to_bool(value) is expected

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("No", False),
            ("n", False),
            ("off", False),
            ("OFF", False),
            ("f", False),
            ("não", False),
            ("nao", False),
            ("", False),
            (False, False),
        ],
    )
    def test_false_values(self, value, expected):
        """Testa conversão de valores falsos."""
        assert TypeConverter.to_bool(value) is expected

    @pytest.mark.parametrize("value", ["maybe", "2", "yesno", "invalid"])
    def test_invalid_bool_values(self, value):
        """Testa valores inválidos para boolean."""
        with pytest.raises(ValidationError) as exc_info:
            TypeConverter.to_bool(value)
        assert "boolean" in str(exc_info.value)


class TestIntConverter:
    """Testes para conversão de inteiros."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("0", 0),
            ("1", 1),
            ("-1", -1),
            ("42", 42),
            ("  123  ", 123),
            (999, 999),
        ],
    )
    def test_valid_int_conversion(self, value, expected):
        """Testa conversão válida de inteiros."""
        assert TypeConverter.to_int(value) == expected

    @pytest.mark.parametrize("value", ["not_a_number", "12.5", "1.0", ""])
    def test_invalid_int_values(self, value):
        """Testa valores inválidos para inteiro."""
        with pytest.raises(ValidationError) as exc_info:
            TypeConverter.to_int(value)
        assert "int" in str(exc_info.value)


class TestFloatConverter:
    """Testes para conversão de floats."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("0.0", 0.0),
            ("1.5", 1.5),
            ("-3.14", -3.14),
            ("42", 42.0),
            ("  2.718  ", 2.718),
            (3.14, 3.14),
        ],
    )
    def test_valid_float_conversion(self, value, expected):
        """Testa conversão válida de floats."""
        assert TypeConverter.to_float(value) == pytest.approx(expected)

    @pytest.mark.parametrize("value", ["not_a_number", ""])
    def test_invalid_float_values(self, value):
        """Testa valores inválidos para float."""
        with pytest.raises(ValidationError) as exc_info:
            TypeConverter.to_float(value)
        assert "float" in str(exc_info.value)


class TestListConverter:
    """Testes para conversão de listas."""

    @pytest.mark.parametrize(
        "value,delimiter,expected",
        [
            ("a,b,c", ",", ["a", "b", "c"]),
            ("one, two, three", ",", ["one", "two", "three"]),
            ("", ",", []),
            ("single", ",", ["single"]),
            ("a;b;c", ";", ["a", "b", "c"]),
            ("a|b|c", "|", ["a", "b", "c"]),
            (["x", "y"], ",", ["x", "y"]),
        ],
    )
    def test_list_conversion(self, value, delimiter, expected):
        """Testa conversão de strings para listas."""
        assert TypeConverter.to_list(value, delimiter) == expected

    def test_empty_items_are_filtered(self):
        """Testa que itens vazios são removidos."""
        result = TypeConverter.to_list("a,,b,  ,c", ",")
        assert result == ["a", "b", "c"]


class TestDictConverter:
    """Testes para conversão de dicionários."""

    @pytest.mark.parametrize(
        "value,delimiter,expected",
        [
            ("key=value", ",", {"key": "value"}),
            ("a=1,b=2,c=3", ",", {"a": "1", "b": "2", "c": "3"}),
            ("host=localhost, port=8000", ",", {"host": "localhost", "port": "8000"}),
            ("", ",", {}),
            ("a=1;b=2", ";", {"a": "1", "b": "2"}),
            ({"x": "y"}, ",", {"x": "y"}),
        ],
    )
    def test_dict_conversion(self, value, delimiter, expected):
        """Testa conversão de strings para dicionários."""
        assert TypeConverter.to_dict(value, delimiter) == expected

    def test_key_without_value(self):
        """Testa chaves sem valor (= vazio)."""
        result = TypeConverter.to_dict("key1,key2=value2", ",")
        assert result == {"key1": "", "key2": "value2"}

    def test_multiple_equals_signs(self):
        """Testa valores com múltiplos sinais de igual."""
        result = TypeConverter.to_dict("url=http://example.com?q=test", ",")
        assert result == {"url": "http://example.com?q=test"}

"""Чтение JSON-конфигов с внятными ошибками.

Общая утилита для описания сцены и профиля стиля. Namespace-пакет `worldgen` тут
специально без тяжёлых зависимостей: этот модуль импортируется и внутри процесса
Blender, где стоит своя интерпретация Python и ставить туда ничего нельзя.
"""

from __future__ import annotations

from typing import Any

Vec3 = tuple[float, float, float]


class ConfigValidationError(ValueError):
    """Конфиг не соответствует схеме. Сообщение всегда указывает путь до поля."""


class Reader:
    """Типобезопасное чтение словаря с накоплением пути до поля."""

    def __init__(self, data: Any, path: str = "$") -> None:
        if not isinstance(data, dict):
            raise ConfigValidationError(f"{path}: ожидался объект, получено {type(data).__name__}")
        self.data: dict[str, Any] = data
        self.path = path

    def _at(self, key: str) -> str:
        return f"{self.path}.{key}"

    def req(self, key: str) -> Any:
        if key not in self.data:
            raise ConfigValidationError(f"{self._at(key)}: обязательное поле отсутствует")
        return self.data[key]

    def str_(self, key: str, default: str | None = None) -> str:
        value = self.data.get(key, default) if default is not None else self.req(key)
        if not isinstance(value, str) or not value:
            raise ConfigValidationError(f"{self._at(key)}: ожидалась непустая строка")
        return value

    def num(self, key: str, default: float | None = None) -> float:
        value = self.data.get(key, default) if default is not None else self.req(key)
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ConfigValidationError(f"{self._at(key)}: ожидалось число")
        return float(value)

    def positive(self, key: str, default: float | None = None) -> float:
        value = self.num(key, default)
        if value <= 0:
            raise ConfigValidationError(f"{self._at(key)}: ожидалось положительное число, {value}")
        return value

    def unit(self, key: str, default: float | None = None) -> float:
        """Число в [0, 1] — сила денойза и прочие нормированные ручки."""
        value = self.num(key, default)
        if not 0.0 <= value <= 1.0:
            raise ConfigValidationError(f"{self._at(key)}: ожидалось число в [0, 1], {value}")
        return value

    def flag(self, key: str, default: bool) -> bool:
        value = self.data.get(key, default)
        if not isinstance(value, bool):
            raise ConfigValidationError(f"{self._at(key)}: ожидалось true/false")
        return value

    def vec3(self, key: str, default: Vec3 | None = None) -> Vec3:
        if key not in self.data:
            if default is None:
                raise ConfigValidationError(f"{self._at(key)}: обязательное поле отсутствует")
            return default
        value = self.data[key]
        if not isinstance(value, list | tuple) or len(value) != 3:
            raise ConfigValidationError(f"{self._at(key)}: ожидались три числа")
        for item in value:
            if isinstance(item, bool) or not isinstance(item, int | float):
                raise ConfigValidationError(f"{self._at(key)}: ожидались три числа")
        return (float(value[0]), float(value[1]), float(value[2]))

    def choice(self, key: str, allowed: tuple[str, ...], default: str | None = None) -> str:
        value = self.str_(key, default)
        if value not in allowed:
            raise ConfigValidationError(
                f"{self._at(key)}: {value!r} не входит в разрешённые: {', '.join(allowed)}"
            )
        return value

    def child(self, key: str, *, optional: bool = False) -> Reader | None:
        if key not in self.data:
            if optional:
                return None
            raise ConfigValidationError(f"{self._at(key)}: обязательный объект отсутствует")
        return Reader(self.data[key], self._at(key))

    def children(self, key: str, *, min_items: int = 0) -> list[Reader]:
        value = self.req(key) if min_items else self.data.get(key, [])
        if not isinstance(value, list):
            raise ConfigValidationError(f"{self._at(key)}: ожидался список")
        if len(value) < min_items:
            raise ConfigValidationError(f"{self._at(key)}: нужен минимум {min_items} элемент(ов)")
        return [Reader(item, f"{self._at(key)}[{i}]") for i, item in enumerate(value)]

    def named_children(self, key: str, *, min_items: int = 0) -> dict[str, Reader]:
        """Объект-словарь, где ключи — имена (уровни поводка, например)."""
        value = self.req(key) if min_items else self.data.get(key, {})
        if not isinstance(value, dict):
            raise ConfigValidationError(f"{self._at(key)}: ожидался объект")
        if len(value) < min_items:
            raise ConfigValidationError(f"{self._at(key)}: нужен минимум {min_items} элемент(ов)")
        return {name: Reader(item, f"{self._at(key)}.{name}") for name, item in value.items()}


__all__ = ["ConfigValidationError", "Reader", "Vec3"]

from datetime import datetime
from typing import Any, Optional


class TaskValidationError(Exception):
    """Ошибка проверки задачи"""
    pass

class InvalidTaskIdError(TaskValidationError):
    """Ошибка при неверном id"""
    pass

class InvalidPayloadError(TaskValidationError):
    """Ошибка при неверном payload"""
    pass

class InvalidPriorityError(TaskValidationError):
    """Ошибка при неверном приоритете"""
    pass

class InvalidStatusError(TaskValidationError):
    """Ошибка при неверном статусе"""
    pass

class InvalidAgeError(TaskValidationError):
    """Ошибка при неверном возрасте задачи"""
    pass

class PriorityDescriptor:
    """Data descriptor для приоритета задачи"""
    def __set_name__(self, owner: type, name: str) -> None:
        self.public_name = name
        self.private_name = f"_{name}"
    
    def __get__(self, obj: Optional[Any], objtype: Optional[type] = None) -> Any:
        if obj is None:
            return self
        return getattr(obj, self.private_name)
    
    def __set__(self, obj: Any, value: int) -> None:
        if not isinstance(value, int):
            raise InvalidPriorityError("Значение приоритета должно быть целым числом")
        if value < 1 or value > 10:
            raise InvalidPriorityError("Значение приоритета должно быть от 1 до 10")
        setattr(obj, self.private_name, value)

    def __delete__(self, obj: Any) -> None:
        raise InvalidPriorityError("Невозможно удалить приоритет задачи")


class StatusDescriptor:
    """Data descriptor для статуса задачи"""
    
    def __set_name__(self, owner: type, name: str) -> None:
        self.public_name = name
        self.private_name = f"_{name}"
    
    def __get__(self, obj: Optional[Any], objtype: Optional[type] = None) -> Any:
        if obj is None:
            return self
        return getattr(obj, self.private_name, "создана")
    
    def __set__(self, obj: Any, value: str) -> None:
        if not isinstance(value, str):
            raise InvalidStatusError("Статус задачи должен быть строкой")
        value_lower = value.lower()
        if value_lower not in ["создана", "выполняется", "завершена"]:
            raise InvalidStatusError("Невозможный статус задачи. Допустимые значения: 'создана', 'выполняется', 'завершена'")
        setattr(obj, self.private_name, value_lower)
    
    def __delete__(self, obj: Any) -> None:
        raise InvalidStatusError("Невозможно удалить статус задачи")

class AgeDescriptor:
    """Non-data descriptor для вычисления возраста задачи"""
    
    def __get__(self, obj: Optional[Any], objtype: Optional[type] = None) -> Any:
        if obj is None:
            return self
        if not hasattr(obj, '_created_at'):
            raise InvalidAgeError("Задача не имеет времени создания")
        age = (datetime.now() - obj._created_at).total_seconds()
        return int(age)


class Task:
    """Класс задачи с инкапсуляцией и валидацией состояния"""
    
    priority = PriorityDescriptor()
    status = StatusDescriptor()
    age = AgeDescriptor()
    
    def __init__(self, id: str, payload: str, priority: int = 3, status: str = "создана") -> None:
        """Инициализация задачи"""
        self._validate_id(id)
        self._id = id
        self._validate_payload(payload)
        self._payload = payload.strip()
        self.priority = priority
        self.status = status
        self._created_at = datetime.now()
    
    def _validate_id(self, id: str) -> None:
        """Валидация идентификатора задачи"""
        if not isinstance(id, str):
            raise InvalidTaskIdError("ID должен быть строкой")
        if not id.strip():
            raise InvalidTaskIdError("ID не может быть пустым")
    
    def _validate_payload(self, payload: str) -> None:
        """Валидация содержимого задачи"""
        if not isinstance(payload, str):
            raise InvalidPayloadError("Payload должен быть строкой")
        if not payload.strip():
            raise InvalidPayloadError("Payload не может быть пустым")
        if len(payload) > 2000:
            raise InvalidPayloadError("Payload не может быть длиннее 2000 символов")
    
    @property
    def id(self) -> str:
        """Предоставление доступа чтения к защищенному аттрибуту _id"""
        return self._id
    
    @property
    def payload(self) -> str:
        """Предоставление доступа чтения к защищенному аттрибуту _payload"""
        return self._payload
    
    @property
    def created_at(self) -> datetime:
        """Предоставление доступа чтения к защищенному аттрибуту _created_at"""
        return self._created_at
    
    @property
    def is_in_progress(self) -> bool:
        """Проверка на нахождение задачи на этапе выполнения"""
        return self.status == "выполняется"
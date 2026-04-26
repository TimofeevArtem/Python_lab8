import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from src.contracts.task import *
import time
from src.task_queue.task_queue import *


def tasks_list():
    return [
        Task(id="1", payload="Task1", priority=8, status="создана"),
        Task(id="2", payload="Task2", priority=3, status="выполняется"),
        Task(id="3", payload="Task3", priority=9, status="выполняется"),
        Task(id="4", payload="Task4", priority=2, status="завершена"),
        Task(id="5", payload="Task5", priority=7, status="создана"),
    ]

class TestPriorityDescriptor:
    """Тесты для PriorityDescriptor"""
    def test_priority_valid_values(self):
        """Тест принятия валидных значений"""
        task = Task(id="1", payload="Test", priority=5)
        assert task.priority == 5
        
        task.priority = 1
        assert task.priority == 1
        
        task.priority = 10
        assert task.priority == 10
    
    def test_priority_invalid_values(self):
        """Тест исключений приоритета"""
        task = Task(id="1", payload="Test", priority=3)
        
        with pytest.raises(InvalidPriorityError, match="должно быть целым числом"):
            task.priority = "5"
        
        with pytest.raises(InvalidPriorityError, match="должно быть целым числом"):
            task.priority = 3.14
        
        with pytest.raises(InvalidPriorityError, match="должно быть целым числом"):
            task.priority = None
    
    def test_priority_values_out_of_range(self):
        """Тест приоритета вне диапазона от 1 до 10"""
        task = Task(id="1", payload="Test", priority=3)
        with pytest.raises(InvalidPriorityError, match="от 1 до 10"):
            task.priority = 0
        with pytest.raises(InvalidPriorityError, match="от 1 до 10"):
            task.priority = 11
        with pytest.raises(InvalidPriorityError, match="от 1 до 10"):
            task.priority = -5
    
    def test_priority_cannot_be_deleted(self):
        """Тест на запрет удаления приоритета"""
        task = Task(id="1", payload="Test", priority=5)
        with pytest.raises(InvalidPriorityError, match="Невозможно удалить"):
            del task.priority
    
    def test_priority_default_value(self):
        """Тест на значение приоритета по умолчанию"""
        task = Task(id="1", payload="Test")
        assert task.priority == 3

class TestStatusDescriptor:
    """Тесты для StatusDescriptor"""
    def test_status_accepts_valid_values(self):
        """Тест принятия корректных статусов"""
        task = Task(id="1", payload="Test", status="создана")
        assert task.status == "создана"
        
        task.status = "выполняется"
        assert task.status == "выполняется"
        
        task.status = "завершена"
        assert task.status == "завершена"
    
    def test_status_to_low_register(self):
        """Тест на приведение к нижнему регистру статусов"""
        task = Task(id="1", payload="Test", status="создана")
        
        task.status = "СОЗДАНА"
        assert task.status == "создана"
        
        task.status = "Выполняется"
        assert task.status == "выполняется"
        
        task.status = "ЗаВерШена"
        assert task.status == "завершена"
    
    def test_status_invalid_values(self):
        """Тест на некорректные статусы"""
        task = Task(id="1", payload="Test")
        
        with pytest.raises(InvalidStatusError, match="Невозможный статус"):
            task.status = "неизвестно"

        with pytest.raises(InvalidStatusError, match="Невозможный статус"):
            task.status = "в ожидании"
        
        with pytest.raises(InvalidStatusError, match="Невозможный статус"):
            task.status = ""
    
    def test_status_non_string_values(self):
        """Тест на нестроковые статусы"""
        task = Task(id="1", payload="Test")
        
        with pytest.raises(InvalidStatusError, match="должен быть строкой"):
            task.status = 123
        
        with pytest.raises(InvalidStatusError, match="должен быть строкой"):
            task.status = None
    
    def test_status_cannot_be_deleted(self):
        """Тест на запрет удаления статуса"""
        task = Task(id="1", payload="Test", status="создана")
        
        with pytest.raises(InvalidStatusError, match="Невозможно удалить"):
            del task.status
    
    def test_status_default_value(self):
        """Тест статуса по умолчанию"""
        task = Task(id="1", payload="Test")
        assert task.status == "создана"

class TestAgeDescriptor:
    """Тесты для AgeDescriptor"""
    def test_age_calculates_correctly_with_sleep(self):
        """Тест вычисления возраста"""
        task = Task(id="1", payload="Test")
        age_1 = task.age
        assert age_1 == 0
        time.sleep(2)

        age_2 = task.age
        assert age_2 == 2
    
    def test_age_increases_over_time(self):
        """Тест увеличения возраста"""
        task = Task(id="1", payload="Test")
        age_1 = task.age
        time.sleep(1)
        age_2 = task.age
        time.sleep(1)
        age_3 = task.age
        
        assert age_3 > age_2 > age_1
    
    def test_age_returns_integer(self):
        """Тест, что возраст возвращается целым числом"""
        task = Task(id="1", payload="Test")
        time.sleep(0.5)
        
        age = task.age
        assert isinstance(age, int)
        assert age == int(age)
    
    def test_age(self):
        """Тест возраста"""
        task = Task(id="1", payload="Test")
        time.sleep(3)
        
        age = task.age
        assert age == 3
    
    def test_age_descriptor_returns_self_on_class_access(self):
        """Тест доступа к дескриптору через класс"""
        assert isinstance(Task.age, AgeDescriptor)
    
    def test_age_raises_error_if_no_created_at(self):
        """Тест ошибки при отсутствии _created_at"""
        task = Task(id="1", payload="Test")
        del task._created_at
        
        with pytest.raises(InvalidAgeError, match="не имеет времени создания"):
            _ = task.age
    
    def test_age_multiple_accesses(self):
        """Тест множественного доступа к возрасту"""
        task = Task(id="1", payload="Test")
        ages = []
        for _ in range(5):
            ages.append(task.age)
            time.sleep(0.5)
        for i in range(1, len(ages)):
            assert ages[i] >= ages[i-1]
    
    def test_age_with_short_sleep(self):
        """Тест с очень маленькой задержкой"""
        task = Task(id="1", payload="Test")
        time.sleep(0.1)
        age = task.age
        assert age == 0


class TestTaskValidation:
    """Тесты валидации Task"""
    def test_validation_on_creation_with_valid_data(self):
        """Тест создания с корректными данными"""
        task = Task(
            id="task-123",
            payload="Valid task description",
            priority=7,
            status="выполняется"
        )
        assert task.id == "task-123"
        assert task.payload == "Valid task description"
        assert task.priority == 7
        assert task.status == "выполняется"
        assert isinstance(task.created_at, datetime)
    
    def test_invalid_id_raises_error(self):
        """Тест ошибки при некорректном ID"""
        with pytest.raises(InvalidTaskIdError, match="должен быть строкой"):
            Task(id=123, payload="Test")
        
        with pytest.raises(InvalidTaskIdError, match="не может быть пустым"):
            Task(id="", payload="Test")
        
        with pytest.raises(InvalidTaskIdError, match="не может быть пустым"):
            Task(id="   ", payload="Test")
    
    def test_invalid_payload_raises_error(self):
        """Тест ошибки при некорректном payload"""
        with pytest.raises(InvalidPayloadError, match="должен быть строкой"):
            Task(id="1", payload=123)
        
        with pytest.raises(InvalidPayloadError, match="не может быть пустым"):
            Task(id="1", payload="")
        
        with pytest.raises(InvalidPayloadError, match="не может быть пустым"):
            Task(id="1", payload="   ")
        
        long_payload = "a" * 2001
        with pytest.raises(InvalidPayloadError, match="не может быть длиннее 2000"):
            Task(id="1", payload=long_payload)
    
    def test_payload_strip(self):
        """Тест обрезки пробелов в payload"""
        task = Task(id="1", payload="  Hello World  ")
        assert task.payload == "Hello World"
    
    def test_invalid_priority_on_creation(self):
        """Тест ошибки при некорректном приоритете при создании"""
        with pytest.raises(InvalidPriorityError):
            Task(id="1", payload="Test", priority=0)
        
        with pytest.raises(InvalidPriorityError):
            Task(id="1", payload="Test", priority=11)
        
        with pytest.raises(InvalidPriorityError):
            Task(id="1", payload="Test", priority="5")
    
    def test_invalid_status_on_creation(self):
        """Тест ошибки при некорректном статусе при создании"""
        with pytest.raises(InvalidStatusError):
            Task(id="1", payload="Test", status="invalid")
        
        with pytest.raises(InvalidStatusError):
            Task(id="1", payload="Test", status=123)


class TestTaskProperties:
    """Тесты property атрибутов Task"""
    def test_id_is_readonly(self):
        """Тест, что id доступен только для чтения"""
        task = Task(id="task1", payload="Test")
        assert task.id == "task1"
        
        with pytest.raises(AttributeError):
            task.id = "new_id"
    
    def test_payload_is_readonly(self):
        """Тест, что payload доступен только для чтения"""
        task = Task(id="1", payload="Test")
        assert task.payload == "Test"
        
        with pytest.raises(AttributeError):
            task.payload = "New payload"
    
    def test_created_at_is_readonly(self):
        """Тест, что created_at доступен только для чтения"""
        task = Task(id="1", payload="Test")
        created_at = task.created_at
        
        with pytest.raises(AttributeError):
            task.created_at = datetime.now()
    
    def test_is_in_progress_property(self):
        """Тест вычисляемого свойства is_in_progress"""
        task = Task(id="1", payload="Test", status="создана")
        assert task.is_in_progress is False
        
        task.status = "выполняется"
        assert task.is_in_progress is True
        
        task.status = "завершена"
        assert task.is_in_progress is False
    
    def test_is_in_progress_readonly(self):
        """Тест, что is_in_progress доступен только для чтения"""
        task = Task(id="1", payload="Test")
        
        with pytest.raises(AttributeError):
            task.is_in_progress = True


class TestTaskEncapsulation:
    """Тесты инкапсуляции"""
    def test_private_attributes_are_protected(self):
        """Тест, что приватные атрибуты недоступны напрямую"""
        task = Task(id="1", payload="Test")

        assert hasattr(task, '_id')
        assert hasattr(task, '_payload')
        assert hasattr(task, '_created_at')
        assert hasattr(task, '_priority')
        assert hasattr(task, '_status')
    
    def test_cannot_set_private_attributes_directly(self):
        """Тест, что нельзя установить приватные атрибуты в обход дескрипторов"""
        task = Task(id="1", payload="Test")
        task._priority = 99
        task.priority = 5
        assert task.priority == 5


class TestTaskExceptionHierarchy:
    """Тесты исключений"""
    def test_exception_inheritance(self):
        """Тест наследования исключений"""
        assert issubclass(InvalidTaskIdError, TaskValidationError)
        assert issubclass(InvalidPayloadError, TaskValidationError)
        assert issubclass(InvalidPriorityError, TaskValidationError)
        assert issubclass(InvalidStatusError, TaskValidationError)
        assert issubclass(InvalidAgeError, TaskValidationError)
    
    def test_catch_all_validation_errors(self):
        """Тест перехвата всех ошибок валидации"""
        with pytest.raises(TaskValidationError):
            Task(id="", payload="Test")
        
        with pytest.raises(TaskValidationError):
            Task(id="1", payload="")
        
        with pytest.raises(TaskValidationError):
            Task(id="1", payload="Test", priority=0)


class TestTaskEdgeCases:
    """Тесты граничных случаев"""
    def test_max_payload_length(self):
        """Тест максимальной длины payload"""
        payload = "a" * 2000
        task = Task(id="1", payload=payload)
        assert len(task.payload) == 2000
    
    def test_min_priority(self):
        """Тест минимального приоритета"""
        task = Task(id="1", payload="Test", priority=1)
        assert task.priority == 1
    
    def test_max_priority(self):
        """Тест максимального приоритета"""
        task = Task(id="1", payload="Test", priority=10)
        assert task.priority == 10
    
    def test_special_characters_in_payload(self):
        """Тест спецсимволов в payload"""
        payload = "!@#$%^&*()\n\t\\\"'"
        task = Task(id="1", payload=payload)
        assert task.payload == payload
    
    def test_numeric_string_id(self):
        """Тест ID в виде цифровой строки"""
        task = Task(id="12345", payload="Test")
        assert task.id == "12345"


class TestTaskDescriptorInteraction:
    """Тесты взаимодействия дескрипторов"""
    def test_priority_and_status_independent(self):
        """Тест независимости приоритета и статуса"""
        task = Task(id="1", payload="Test", priority=5, status="создана")
        task.priority = 8
        task.status = "выполняется"
        
        assert task.priority == 8
        assert task.status == "выполняется"
    
    def test_age_updates_after_status_change(self):
        """Тест, что возраст не зависит от статуса"""
        task = Task(id="1", payload="Test")
        age_before = task.age
        
        task.status = "выполняется"
        age_after = task.age
        
        assert age_after >= age_before


def test_task_creation_timestamp():
    """Тест временной метки создания"""
    before = datetime.now()
    task = Task(id="1", payload="Test")
    after = datetime.now()
    
    assert before <= task.created_at <= after

class TestTaskQueueInit:
    """Тесты инициализации TaskQueue"""
    def test_init_empty(self):
        """Создание пустой очереди"""
        queue = TaskQueue()
        assert len(queue) == 0
    
    def test_init_with_tasks(self):
        """Создание очереди с начальными задачами"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        assert len(queue) == 5


class TestTaskQueueAdd:
    """Тесты добавления задач"""
    def test_add_single_task(self):
        """Добавление одной задачи"""
        queue = TaskQueue()
        task = Task(id="1", payload="Test")
        queue.add(task)
        assert len(queue) == 1


class TestTaskQueueGetItem:
    """Тесты доступа по индексу"""
    def test_get_by_index(self):
        """Доступ к задаче по индексу"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        assert queue[0].id == "1"
        assert queue[4].id == "5"
    
    def test_index_error(self):
        """Выход за границы вызывает IndexError"""
        queue = TaskQueue()
        with pytest.raises(IndexError):
            _ = queue[0]


class TestTaskQueueFindById:
    """Тесты поиска по ID"""
    def test_find_existing_task(self):
        """Поиск существующей задачи"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        task = queue.find_task_by_id("3")
        assert task is not None
        assert task.payload == "Task3"
    
    def test_find_non_existent_task(self):
        """Поиск несуществующей задачи"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        task = queue.find_task_by_id("99")
        assert task is None


class TestTaskQueueIteration:
    """Тесты итерации"""
    def test_iterate_all_tasks(self):
        """Итерация по всем задачам очереди"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        ids = [task.id for task in queue]
        assert ids == ["1", "2", "3", "4", "5"]
    
    def test_len_after_iteration(self):
        """Длина очереди не меняется после итерации"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        list(queue)
        assert len(queue) == 5
    
    def test_stop_iteration(self):
        """Проверка StopIteration"""
        queue = TaskQueue()
        iterator = iter(queue)
        with pytest.raises(StopIteration):
            next(iterator)


class TestTaskQueueFilter:
    """Тесты фильтрации через filter()"""
    def test_filter_by_status(self):
        """Фильтр по статусу"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter(status="создана"))
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "5"
    
    def test_filter_by_min_priority(self):
        """Фильтр по минимальному приоритету"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter(min_priority=7))
        assert len(result) == 3
    
    def test_filter_by_max_priority(self):
        """Фильтр по максимальному приоритету"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter(max_priority=3))
        assert len(result) == 2
    
    def test_filter_by_priority_range(self):
        """Фильтр по диапазону приоритетов"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter(min_priority=3, max_priority=7))
        assert len(result) == 2
    
    def test_filter_by_payload_contains(self):
        """Фильтр по подстроке в payload"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter(payload_contains="Task"))
        assert len(result) == 5
    
    def test_filter_empty(self):
        """Фильтр без критериев возвращает все"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter())
        assert len(result) == 5


class TestTaskQueueFilterMethods:
    """Тесты методов фильтрации"""
    def test_filter_by_status_method(self):
        """Метод filter_by_status"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter_by_status("выполняется"))
        assert len(result) == 2
    
    def test_filter_by_priority_method(self):
        """Метод filter_by_priority"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter_by_priority(7, 9))
        ids = [t.id for t in result]
        assert ids == ["1", "3", "5"]
    
    def test_filter_by_payload_method(self):
        """Метод filter_by_payload"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.filter_by_payload("Task"))
        assert len(result) == 5
        assert result[0].id == "1"


class TestTaskQueueGenerators:
    """Тесты генераторных методов"""
    def test_urgent_tasks(self):
        """Генератор urgent_tasks"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.urgent_tasks())
        assert len(result) == 3
    
    def test_completed_tasks(self):
        """Генератор completed_tasks"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.completed_tasks())
        assert len(result) == 1
        assert result[0].id == "4"
    
    def test_urgent_in_progress_tasks(self):
        """Конвейер urgent_in_progress_tasks"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.urgent_in_progress_tasks())
        assert len(result) == 1
        assert result[0].id == "3"
    
    def test_get_tasks_older_than(self):
        """Генератор get_tasks_older_than"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        time.sleep(1)
        result = list(queue.get_tasks_older_than(0))
        assert len(result) == 5
    
    def test_get_tasks_older_than_none(self):
        """Задачи не старше порога"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = list(queue.get_tasks_older_than(9999))
        assert len(result) == 0


class TestTaskQueueFirstInProgress:
    """Тесты get_first_high_priority_in_progress"""
    def test_returns_first_match(self):
        """Возвращает первую подходящую задачу"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        task = queue.get_first_high_priority_in_progress()
        assert task is not None
        assert task.id == "3"
    
    def test_returns_none_when_no_match(self):
        """Возвращает None если нет подходящих"""
        tasks = [Task(id="1", payload="Test", priority=5, status="создана"),]
        queue = TaskQueue(tasks)
        task = queue.get_first_high_priority_in_progress()
        assert task is None


class TestTaskQueueChangePriority:
    """Тесты изменения приоритета"""
    def test_change_priority_success(self):
        """Успешное изменение приоритета"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        updated = queue.change_priority("1", 10)
        assert updated.priority == 10
    
    def test_change_priority_not_found(self):
        """Ошибка при изменении несуществующей задачи"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        with pytest.raises(ValueError, match="не найдена"):
            queue.change_priority("99", 5)


class TestTaskQueueChangeStatus:
    """Тесты изменения статуса"""
    def test_change_status_created_to_in_progress(self):
        """Переход от статуса создана к выполняется"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        updated = queue.change_status("1")
        assert updated.status == "выполняется"
    
    def test_change_status_in_progress_to_completed(self):
        """Переход от статуса выполняется к завершена"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        updated = queue.change_status("2")
        assert updated.status == "завершена"
    
    def test_change_status_completed_raises_error(self):
        """Нельзя изменить статус завершённой задачи"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        with pytest.raises(ValueError, match="Невозможно изменить статус завершённой"):
            queue.change_status("4")
    
    def test_change_status_not_found(self):
        """Ошибка при изменении несуществующей задачи"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        with pytest.raises(ValueError, match="не найдена"):
            queue.change_status("99")


class TestReusableTaskQueue:
    """Тесты ReusableTaskQueue"""
    def test_multiple_iterations(self):
        """Возможность повторного обхода очереди"""
        tasks = tasks_list()
        queue = ReusableTaskQueue(tasks)
        first_pass = list(queue)
        second_pass = list(queue)
        assert len(first_pass) == 5
        assert len(second_pass) == 5
    
    def test_inherits_from_taskqueue(self):
        """Является наследником TaskQueue"""
        queue = ReusableTaskQueue()
        assert isinstance(queue, TaskQueue)
    
    def test_multiple_iterations_independent(self):
        """Итераторы независимы друг от друга"""
        tasks = tasks_list()
        queue = ReusableTaskQueue(tasks)
        it1 = iter(queue)
        it2 = iter(queue)
        next(it1)
        assert next(it1).id == "2"
        assert next(it2).id == "1"


class TestTaskIterator:
    """Тесты TaskIterator"""
    def test_iterator_class(self):
        """Создание и использование TaskIterator"""
        tasks = tasks_list()
        iterator = TaskIterator(tasks)
        result = list(iterator)
        assert len(result) == 5
    
    def test_iterator_is_iterator(self):
        """Итератор является итератором"""
        tasks = tasks_list()
        iterator = TaskIterator(tasks)
        assert iter(iterator) is iterator
    
    def test_iterator_stop_iteration(self):
        """StopIteration после исчерпания"""
        tasks = tasks_list()
        iterator = TaskIterator(tasks)
        for _ in range(5):
            next(iterator)
        with pytest.raises(StopIteration):
            next(iterator)


class TestTaskQueueLazyEvaluation:
    """Тесты ленивых вычислений"""
    def test_filter_is_lazy(self):
        """Фильтр возвращает генератор, а не список"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = queue.filter_by_status("создана")
        assert hasattr(result, '__iter__')
        assert not hasattr(result, '__len__')
    
    def test_urgent_is_generator(self):
        """urgent_tasks возвращает генератор"""
        tasks = tasks_list()
        queue = TaskQueue(tasks)
        result = queue.urgent_tasks()
        assert hasattr(result, '__iter__')
        assert not hasattr(result, '__len__')
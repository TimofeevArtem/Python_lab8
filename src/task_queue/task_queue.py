from collections.abc import Iterable, Iterator
from typing import Optional
from datetime import datetime

from src.contracts.task import Task


class TaskQueue:
    """Очередь задач с итерацией, фильтрацией и ленивой обработкой"""
    def __init__(self, tasks: Optional[Iterable[Task]] = None) -> None:
        """Инициализация очереди задач"""
        self._tasks: list[Task] = []
        self._task_index: dict[str, Task] = {}
        if tasks:
            for task in tasks:
                self.add(task)
    
    def add(self, task: Task) -> None:
        """Добавить задачу в очередь"""
        if task.id in self._task_index:
            raise ValueError(f"Задача с ID '{task.id}' уже существует в очереди")
        self._tasks.append(task)
        self._task_index[task.id] = task
    
    def __len__(self) -> int:
        """Вернуть количество задач в очереди"""
        return len(self._tasks)
    
    def __getitem__(self, index: int) -> Task:
        """Доступ к задаче по индексу"""
        return self._tasks[index]
    
    def __iter__(self) -> Iterator[Task]:
        """Одноразовый итератор для всех задач очереди"""
        return TaskIterator(self._tasks)
    
    def get_tasks(self) -> list[Task]:
        """Вернуть копию списка задач"""
        return self._tasks.copy()
    
    def filter(self, status: Optional[str] = None, min_priority: Optional[int] = None, max_priority: Optional[int] = None, payload_contains: Optional[str] = None) -> Iterator[Task]:
        """Генераторная функция ленивой фильтрации задач"""
        for task in self._tasks:
            if status is not None and task.status != status:
                continue
            if min_priority is not None and task.priority < min_priority:
                continue
            if max_priority is not None and task.priority > max_priority:
                continue
            if payload_contains is not None and payload_contains not in task.payload:
                continue
            yield task
    
    def filter_by_status(self, status: str) -> Iterator[Task]:
        """Генераторная функция ленивой фильтрации по статусу"""
        for task in self._tasks:
            if task.status == status:
                yield task
    
    def filter_by_priority(self, min_priority: int, max_priority: int) -> Iterator[Task]:
        """Генераторная функция ленивой фильтрации по диапазону приоритетов"""
        for task in self._tasks:
            if min_priority <= task.priority <= max_priority:
                yield task
    
    def filter_by_payload(self, substring: str) -> Iterator[Task]:
        """Генераторная функция ленивой фильтрации по содержимому payload"""
        for task in self._tasks:
            if substring in task.payload:
                yield task
    
    def urgent_tasks(self) -> Iterator[Task]:
        """Генераторное выражение задачи с высоким приоритетом"""
        return (task for task in self._tasks if task.priority >= 7)
    
    def completed_tasks(self) -> Iterator[Task]:
        """Генераторное выражение завершённые задачи """
        return (task for task in self._tasks if task.status == "завершена")
    
    def urgent_in_progress_tasks(self) -> Iterator[Task]:
        """Конвейер срочные задачи в процессе выполнения"""
        urgent = (t for t in self._tasks if t.priority >= 7)
        return (t for t in urgent if t.status == "выполняется")
    
    def get_tasks_older_than(self, seconds: int) -> Iterator[Task]:
        """Генераторная функция получить задачи старше указанного количества секунд"""
        now = datetime.now()
        for task in self._tasks:
            age = (now - task.created_at).total_seconds()
            if age > seconds:
                yield task
    
    def get_first_high_priority_in_progress(self) -> Optional[Task]:
        """Обработка StopIteration первая выполняемая задача с высоким приоритетом"""
        filtered = self.urgent_in_progress_tasks()
        try:
            return next(filtered)
        except StopIteration:
            return None
    
    def find_task_by_id(self, task_id: str) -> Optional[Task]:
        """Найти задачу по ID"""
        return self._task_index.get(task_id)
    
    def change_priority(self, task_id: str, new_priority: int) -> Optional[Task]:
        """Изменить приоритет задачи"""
        task = self.find_task_by_id(task_id)
        if task is None:
            raise ValueError(f"Задача с ID '{task_id}' не найдена")
        
        task.priority = new_priority
        return task
    
    def change_status(self, task_id: str) -> Optional[Task]:
        """Изменить статус задачи"""
        task = self.find_task_by_id(task_id)
        if task is None:
            raise ValueError(f"Задача с ID '{task_id}' не найдена")
        
        if task.status == "завершена":
            raise ValueError(f"Невозможно изменить статус завершённой задачи '{task_id}'")
        
        status_cycle = {
            "создана": "выполняется",
            "выполняется": "завершена"
        }
        
        task.status = status_cycle[task.status]
        return task
    
    def __repr__(self) -> str:
        return f"TaskQueue(tasks={len(self._tasks)})"


class TaskIterator(Iterator[Task]):
    """Итератор для TaskQueue"""
    def __init__(self, tasks: list[Task]) -> None:
        self._tasks = tasks
        self._index = 0
    
    def __iter__(self) -> Iterator[Task]:
        return self
    
    def __next__(self) -> Task:
        if self._index >= len(self._tasks):
            raise StopIteration
        task = self._tasks[self._index]
        self._index += 1
        return task


class ReusableTaskQueue(TaskQueue):
    """Очередь задач с возможностью повторного обхода"""
    def __iter__(self) -> Iterator[Task]:
        """Возвращает новый итератор при каждом вызове"""
        return TaskIterator(self._tasks.copy())
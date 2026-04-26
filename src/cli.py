from pathlib import Path
from typing import Any, Optional
import typer
from typer import Typer
from src.contracts.task import Task
from src.inbox.core import InboxApp
from src.sources.repository import REGISTRY
from src.task_queue.task_queue import ReusableTaskQueue, TaskQueue
import src.sources.json
import src.sources.stdin

cli = Typer(no_args_is_help=True)

@cli.command("plugins")
def plugins_list() -> None:
    """Показать список всех зарегистрированных плагинов"""
    typer.echo("Доступные плагины:")
    for name in sorted(REGISTRY):
        typer.echo(f"  - {name}")

def _build_sources(stdin: bool, jsonl: list[Path]) -> list[Any]:
    sources: list[Any] = []
    if stdin:
        sources.append(REGISTRY["stdin"]())
    for path in jsonl:
        sources.append(REGISTRY["file-jsonl"](path))
    return sources

def _load_tasks_from_sources(stdin: bool, jsonl: list[Path]) -> list[Task]:
    raw_sources = _build_sources(stdin, jsonl)
    inbox = InboxApp(raw_sources)
    return list(inbox.iter_tasks())

def _display_tasks(tasks: list[Task]) -> None:
    if not tasks:
        typer.echo("Задачи не найдены.")
        return
    for task in tasks:
        typer.echo("\n_______________________")
        typer.echo(f"ID: {task.id}")
        typer.echo(f"Payload: {task.payload}")
        typer.echo(f"Priority: {task.priority}")
        typer.echo(f"Status: {task.status}")
        typer.echo(f"Age: {task.age} секунд")
        typer.echo("_______________________\n")
    typer.echo(f"Всего: {len(tasks)}")


def _display_iterator_tasks(iterator) -> None:
    tasks = list(iterator)
    _display_tasks(tasks)


@cli.command("read")
def read(
    stdin: bool = typer.Option(False, "--stdin", help="Читать задачи из stdin"),
    jsonl: list[Path] = typer.Option(
        help="Читать задачи из JSONL файлов",
        default_factory=list,
        exists=True,
        dir_okay=False,
        readable=True,
    ),
    contains: Optional[str] = typer.Option(None, "--contains", help="Фильтр по подстроке"),):
    """Прочитать задачи из указанных источников и отобразить их"""
    tasks = _load_tasks_from_sources(stdin, jsonl)
    
    if contains:
        tasks = [t for t in tasks if contains in t.payload]
    
    _display_tasks(tasks)


@cli.command("interactive")
def interactive(
    stdin: bool = typer.Option(False, "--stdin", help="Загрузить задачи из stdin при запуске"),
    jsonl: list[Path] = typer.Option(
        help="Загрузить задачи из JSONL файлов при запуске",
        default_factory=list,
        exists=True,
        dir_okay=False,
        readable=True,
    ),
):
    """Интерактивный режим для работы с очередью задач"""
    initial_tasks = _load_tasks_from_sources(stdin, jsonl)
    queue = ReusableTaskQueue(initial_tasks)
    
    while True:
        typer.echo("\n_______________________")
        typer.echo("1. Показать все задачи")
        typer.echo("2. Фильтр по статусу")
        typer.echo("3. Фильтр по диапазону приоритетов")
        typer.echo("4. Фильтр по подстроке в payload")
        typer.echo("5. Показать задачи старше N секунд")
        typer.echo("6. Добавить новую задачу")
        typer.echo("7. Загрузить задачи из tasks.jsonl")
        typer.echo("8. Изменить приоритет задачи")
        typer.echo("9. Изменить статус задачи")
        typer.echo("10. Показать срочные задачи")
        typer.echo("11. Показать срочные выполняемые")
        typer.echo("12. Первая срочная и выполняемая задача")
        typer.echo("13. Выход")
        typer.echo("_______________________\n")
        
        choice = typer.prompt("Введите число")
        
        if choice == "13":
            typer.echo("До свидания!")
            break
        
        elif choice == "1":
            try:
                _display_tasks(list(queue))
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "2":
            typer.echo("Выберите по какому статусу фильтровать:")
            typer.echo("1. Создана")
            typer.echo("2. Выполняется")
            typer.echo("3. Завершена")
            choice_filter = typer.prompt("Введите число")
            try:
                if choice_filter == "1":
                    status = "создана"
                elif choice_filter == "2":
                    status = "выполняется"
                elif choice_filter == "3":
                    status = "завершена"
                else:
                    typer.echo("Неверный ввод")
                    continue

                _display_iterator_tasks(queue.filter_by_status(status))
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "3":
            min_prio = typer.prompt("Минимальный приоритет", type=int, default=1, show_default=False)
            max_prio = typer.prompt("Максимальный приоритет", type=int, default=10, show_default=False)
            try:
                if 1 <= min_prio <= 10 and 1 <= max_prio <= 10 and min_prio <= max_prio:
                    _display_iterator_tasks(queue.filter_by_priority(min_prio, max_prio))
                else:
                    typer.echo("Неверный диапазон приоритетов")
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "4":
            substring = typer.prompt("Введите искомую подстроку")
            try:
                _display_iterator_tasks(queue.filter_by_payload(substring))
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "5":
            seconds = typer.prompt("Порог возраста в секундах", type=int)
            try:
                _display_iterator_tasks(queue.get_tasks_older_than(seconds))
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "6":
            task_id = typer.prompt("ID")
            payload = typer.prompt("Payload")
            priority = typer.prompt("priority", type=int, default=3)
            status = typer.prompt("status", default="создана")
            try:
                task = Task(id=task_id, payload=payload, priority=priority, status=status)
                queue.add(task)
                typer.echo(f"Задача '{task_id}' добавлена")
            except Exception as e:
                typer.echo(f"Ошибка при создании задачи: {e}")
        
        elif choice == "7":
            jsonl_path = Path("source/tasks.jsonl")
            try:
                if not jsonl_path.exists():
                    typer.echo(f"Ошибка: Файл не найден: {jsonl_path}")
                else:
                    source = REGISTRY["file-jsonl"](jsonl_path)
                    tasks_loaded = 0
                    for task in source.fetch():
                        try:
                            queue.add(task)
                            tasks_loaded += 1
                        except Exception as e:
                            typer.echo(f"Ошибка при добавлении задачи: {e}")
                    typer.echo(f"Загружено задач: {tasks_loaded}")
            except Exception as e:
                typer.echo(f"Ошибка при загрузке файла: {e}")

        elif choice == "8":
            task_id = typer.prompt("ID задачи")
            try:
                task = queue.find_task_by_id(task_id)
                if task is None:
                    typer.echo(f"Задача с ID '{task_id}' не найдена")
                    continue

                new_priority = typer.prompt("Введите новый приоритет", type=int)
                updated_task = queue.change_priority(task_id, new_priority)
                if updated_task:
                    _display_tasks([updated_task])
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "9":
            task_id = typer.prompt("ID задачи")
            try:
                task = queue.find_task_by_id(task_id)
                if task is None:
                    typer.echo(f"Задача с ID '{task_id}' не найдена")
                    continue
                updated_task = queue.change_status(task_id)
                if updated_task:
                    _display_tasks([updated_task])
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "10":
            try:
                _display_iterator_tasks(queue.urgent_tasks())
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "11":
            try:
                _display_iterator_tasks(queue.urgent_in_progress_tasks())
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        elif choice == "12":
            try:
                first_task = queue.get_first_high_priority_in_progress()
                if first_task:
                    _display_tasks([first_task])
                else:
                    typer.echo("Таких задач нет")
            except Exception as e:
                typer.echo(f"Ошибка: {e}")
        
        else:
            typer.echo("Неверный ввод")
# Lab 8 - Система управления задачами
## Очередь задач поддерживающая итерацию, фильтрацию и потоковую обработку задач

### Основные компаненты
- TaskQueue - основной класс очереди задач
- TaskIterator - итератор, ходящий по очереди
- ReusableTaskQueue - очередь задачь, но которую можно обходить несколько раз


### Работа с интерактивным режимом
По сравнению с прошлой ЛР в эту добавлен интерактивный режим.
С самого начала вас встречает список возможностей
```bash 
1. Показать все задачи
2. Фильтр по статусу
3. Фильтр по диапазону приоритетов
4. Фильтр по подстроке в payload
5. Показать задачи старше N секунд
6. Добавить новую задачу
7. Загрузить задачи из tasks.jsonl
8. Изменить приоритет задачи
9. Изменить статус задачи
10. Показать срочные задачи
11. Показать срочные выполняемые
12. Первая срочная и выполняемая задача
13. Выход
```
Все интуитивно понятно и если следовать инструкциям  выходящим по мере работы с приложением, то все будет хорошо.

### Установка

#### Загрузка докер образов
docker pull timofeevartem/python_lab8:latest
docker pull timofeevartem/python_lab8:test

### Основные команды
Запуск приложения в интерактивном режиме:
```bash
docker run -it --rm timofeevartem/python_lab8:latest interactive
```

Все основные команды из ЛР2 работают
ссылка на ЛР2: https://github.com/TimofeevArtem/Python_lab7
+
```bash
#Чтение тасков из файла + запуск в интерактивном режиме
docker run -it --rm timofeevartem/python_lab8:latest interactive --jsonl source/tasks.jsonl
```

## Запуск тестов
```bash
docker run --rm timofeevartem/python_lab8:test

docker run --rm timofeevartem/python_lab8:test pytest tests/test.py -v

docker run --rm timofeevartem/python_lab8:test pytest tests/test.py::TestTask::test_task_creation -v
```

## Ссылка на DockerHub
Docker Hub: https://hub.docker.com/repository/docker/timofeevartem/python_lab8/general
FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install typer

COPY src ./src/
COPY source ./source/
COPY README.md ./
COPY source/tasks.jsonl ./tasks.jsonl
COPY src/task_queue ./task_queue/

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "src.__main__"]

CMD ["--help"]
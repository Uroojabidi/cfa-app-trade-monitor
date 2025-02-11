FROM python:3.9-slim

WORKDIR /app

COPY main.py .
COPY trades.csv .
COPY cfa_standards.csv .
COPY cfa_rules.csv .

RUN pip install csvkit

# Set environment variable for Docker execution
ENV RUNNING_IN_DOCKER=1

CMD ["python", "main.py"]

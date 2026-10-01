FROM python:3.13-slim
WORKDIR /tests
COPY tests/run_tests.py /tests/run_tests.py
COPY fixtures/ /tests/fixtures/
CMD ["python", "/tests/run_tests.py"]

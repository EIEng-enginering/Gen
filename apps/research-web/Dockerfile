FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app /app/app
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations
COPY entrypoint.sh /app/entrypoint.sh
RUN useradd --create-home --uid 10001 genuser && chmod 755 /app/entrypoint.sh
USER genuser
EXPOSE 8765
CMD ["/app/entrypoint.sh"]

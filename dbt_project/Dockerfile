FROM python:3.12-slim

WORKDIR /dbt

# Install dbt-postgres
RUN pip install --no-cache-dir dbt-postgres==1.8.2

# Copy project files
COPY . .

# Override profiles dir so DBT picks up our profiles.yml
ENV DBT_PROFILES_DIR=/dbt

CMD ["sh", "-c", "dbt deps && dbt run && dbt test"]

FROM python:3.11

WORKDIR /app

COPY ./requirements_bookworm.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY ./app /app

# Install necessary packages for bluetooth
RUN apt-get update && apt-get install -y --no-install-recommends \
    bluez \
    libglib2.0-dev

ENTRYPOINT [ "python", "main.py" ]
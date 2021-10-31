FROM python:3.10

RUN apt-get update && \
	apt-get install -y pandoc && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /install
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src
RUN ls -la src

CMD python -m sanic src.app --port=1337 --host=0.0.0.0 --debug

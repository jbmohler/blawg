FROM python:3.10

RUN apt-get update && \
	apt-get install -y pandoc && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /install
COPY requirements.txt .
COPY --from=mecolm-wheel /build/mecolm/mecolm-0.1-py3-none-any.whl .
RUN pip install -r requirements.txt
RUN pip install mecolm-0.1-py3-none-any.whl

COPY src/ src
RUN ls -la src

CMD python -m sanic src.app --port=1337 --host=0.0.0.0 --debug

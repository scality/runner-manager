from prometheus_client import make_asgi_app, Gauge

runners = Gauge("runners", "Number of runners")

runners.set(4)

app = make_asgi_app()
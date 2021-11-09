import os
import asyncio
import concurrent.futures
import sanic
from sanic.log import logger


class Yenot2(sanic.Sanic):
    @staticmethod
    def get_public_basepath(request):
        if "x-original-uri" in request.headers:
            mypath = request.path.lstrip("/")
            public = request.headers["x-original-uri"]
            if len(mypath) and public.endswith(mypath):
                public = public[: -len(mypath)]
            assert public.endswith("/")
            return public
        else:
            return "/"

    def register(self, method, kwargs):
        kwargs.pop("report_title", None)
        # TODO: add to some list

    def get(self, *args, **kwargs):
        self.register("get", kwargs)
        return super().get(*args, **kwargs)

    def put(self, *args, **kwargs):
        self.register("put", kwargs)
        return super().put(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.register("post", kwargs)
        return super().post(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.register("delete", kwargs)
        return super().delete(*args, **kwargs)

    def patch(self, *args, **kwargs):
        self.register("patch", kwargs)
        return super().patch(*args, **kwargs)

    def head(self, *args, **kwargs):
        self.register("head", kwargs)
        return super().head(*args, **kwargs)

    def websocket(self, *args, **kwargs):
        self.register("websocket", kwargs)
        return super().websocket(*args, **kwargs)


from . import postgresql


async def setup_executor(app, loop):
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor())

    # give the DB some time to init
    await asyncio.sleep(5)

    app.pool = await postgresql.create_pool(os.getenv("DB_CONNECTION"))
    app.__class__.dbconn = postgresql.dbconn

    async with app.dbconn() as conn:
        sver = await postgresql.sql_1row(conn, "select version()")

        logger.info(f"Running with DB version {sver}")

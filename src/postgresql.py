import contextlib
import random
import urllib.parse
import aiopg
import psycopg2.extras
import psycopg2.extensions as psyext


async def create_connection(dburl):
    result = urllib.parse.urlsplit(dburl)

    kwargs = {"dbname": result.path[1:]}
    if result.hostname != None:
        kwargs["host"] = result.hostname
    if result.port != None:
        kwargs["port"] = result.port
    if result.username != None:
        kwargs["user"] = result.username
    if result.password != None:
        kwargs["password"] = result.password
    kwargs["cursor_factory"] = psycopg2.extras.NamedTupleCursor

    return await aiopg.connect(**kwargs)


async def create_pool(dburl):
    result = urllib.parse.urlsplit(dburl)

    kwargs = {"dbname": result.path[1:]}
    if result.hostname not in [None, ""]:
        kwargs["host"] = result.hostname
    if result.port != None:
        kwargs["port"] = result.port
    if result.username != None:
        kwargs["user"] = result.username
    if result.password != None:
        kwargs["password"] = result.password
    kwargs["cursor_factory"] = psycopg2.extras.NamedTupleCursor

    return await aiopg.create_pool(**kwargs, minsize=3, maxsize=6)



# to become a method of app
@contextlib.asynccontextmanager
async def dbconn(self):
    for index in range(15):
        if index > 3:
            print(
                f"Attempt #{index} to get a connection from the connection pool",
                flush=True,
            )
        try:
            conn = await self.pool.acquire()
            break
        except psycopg2.pool.PoolError as e:
            if index < 14 and str(e) == "connection pool exhausted":
                time.sleep(random.random() * 0.5 + 0.1)
            else:
                raise
    #ctoken = getattr(request, "cancel_token", None)
    try:
        #if ctoken != None:
        #    self.register_connection(ctoken, conn)
        yield conn
    finally:
        #if ctoken != None:
        #    self.unregister_connection(ctoken, conn)
        await self.pool.release(conn)

from .sqlread import *
from .sqlwrite import *

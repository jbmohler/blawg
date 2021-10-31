import os
import tempfile
import functools
import subprocess
import asyncio
import concurrent.futures
import base64
import yaml
import sanic
import github
import jinja2
from sanic.log import logger

app = sanic.Sanic("blawg like a pro")

GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_BLOG_REPO = os.getenv("GITHUB_BLOG_REPO")

GITHUB_BLOG_DIR = os.getenv("GITHUB_BLOG_DIR")

GITHUB_STATIC_DIR = "/static"

STATIC_TOPMATTER = "topmatter"
STATIC_HEADER = "header"
STATIC_FOOTER = "footer"
STATIC_BOTTOMMATTER = "bottommatter"


@functools.lru_cache()
def get_repo():
    g = github.Github()
    return g.get_repo(f"{GITHUB_USER}/{GITHUB_BLOG_REPO}")


@functools.lru_cache(maxsize=8)
def get_static_file(static):
    repo = get_repo()

    try:
        cfile = repo.get_contents(f"{GITHUB_STATIC_DIR}/{static}")

        raw = base64.b64decode(cfile.content)
        return raw.decode("utf8")
    except:
        print(f"did not find {static}")
        # TODO:  get more precise about exception
        return ""


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


@app.get("/pathdest")
async def pathdest(request):
    await asyncio.sleep(0.1)
    return sanic.text("Done.")


@app.get("/")
async def slashpathtest(request):
    kvs = [f"{k}={v}" for k, v in request.headers.items()]
    kvs.append("")
    kvs.append(f"path={request.path}")
    kvs.append(f"public={get_public_basepath(request)}")
    kvs.append("")
    headers = "<br />".join(kvs)

    headers += (
        f"<br />path={request.path}<br />public={get_public_basepath(request)}<br />"
    )

    dest = f"{get_public_basepath(request)}pathdest"

    return sanic.html(
        f"""
<html>
<body>
{headers}
<a href="{dest}">pathdest</a>
</body>
</html>
"""
    )


@app.get("/dir/<dirpath:path>")
async def get_github_dir(request, dirpath):
    repo = get_repo()

    cfile = repo.get_contents(dirpath)

    def repr(c):
        return f"{c.type}: {c.path}"

    return sanic.text(str([repr(c) for c in cfile]))


@app.get("/commits")
async def get_github_commits(request):
    repo = get_repo()

    commits = repo.get_commits()

    def repr(c):
        lines = [f"{c.author} {c.commit.author.date} {c.sha} {c.commit.message}\n"]
        for f in c.files:
            lines.append(f"\t{f.filename} +{f.additions} -{f.deletions}\n")
        return "".join(lines)

    return sanic.text("".join([repr(c) for c in commits]))


class IndexMeta:
    def __init__(self):
        pass

    @property
    def title(self):
        return "Index"


@app.get("/index")
async def get_github_index(request):
    repo = get_repo()

    async with app.dbconn() as conn:
        posts = await postgresql.sql_rows(conn, "select * from posts")

    cfile = repo.get_contents(f"{GITHUB_BLOG_DIR}")

    def repr(c):
        hyper = c.path.replace(GITHUB_BLOG_DIR, "").strip("/")
        base = get_public_basepath(request)
        return f"<a href='{base}page/{hyper}'>{c.name}</a><br />"

    output = "\n".join([repr(c) for c in cfile])

    topmatter = get_static_file(STATIC_TOPMATTER)
    header = get_static_file(STATIC_HEADER)
    footer = get_static_file(STATIC_FOOTER)
    bottommatter = get_static_file(STATIC_BOTTOMMATTER)

    meta = IndexMeta()

    j = jinja2.Environment()
    t = j.from_string(topmatter)
    topmatter = t.render(repo=repo, meta=meta)

    j = jinja2.Environment()
    t = j.from_string(header)
    header = t.render(repo=repo, meta=meta)

    j = jinja2.Environment()
    t = j.from_string(footer)
    footer = t.render(repo=repo, meta=meta)

    html = f"""
{topmatter}
{header}
{output}
{footer}
{bottommatter}"""

    return sanic.html(html)


@app.get("/rawpage/<blogpath:path>")
async def get_github_rawpage(request, blogpath):
    repo = get_repo()

    cfile = repo.get_contents(blogpath)
    raw = base64.b64decode(cfile.content)
    return sanic.text(raw.decode("utf8"))


MJ_SCRIPT = """ <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"> </script>"""

# Markdown metadata
# https://stackoverflow.com/questions/44215896/markdown-metadata-format


class PageMeta:
    def __init__(self, metaseg, contentfile):
        if metaseg:
            self._meta = yaml.safe_load(metaseg)
        else:
            self._meta = {}
        self._cfile = contentfile

    @property
    def title(self):
        return self._meta.get("title", self._cfile.name)


@app.get("/page/<blogentry:path>")
async def get_github_blog_page(request, blogentry):
    repo = get_repo()

    cfile = repo.get_contents(f"{GITHUB_BLOG_DIR}/{blogentry}")
    raw = base64.b64decode(cfile.content)

    loop = asyncio.get_running_loop()

    with tempfile.TemporaryDirectory() as tempdir:
        iname = os.path.join(tempdir, "temp.md")
        oname = os.path.join(tempdir, "temp.html")

        content = raw.decode("utf8")
        metaseg = None
        if content.startswith("---"):
            splits = content.split("---", 2)
            if len(splits) < 3:
                metaseg, content = None, content
            else:
                _, metaseg, content = splits

        meta = PageMeta(metaseg, cfile)

        with open(iname, "w") as ff:
            ff.write(content)

        await loop.run_in_executor(
            None, subprocess.run, ["pandoc", "--mathjax", iname, "-o", oname]
        )
        # os.system("pandoc --standalone --mathjax -f markdown -t html temp.md -o temp.html")

        with open(oname, "r") as ff:
            output = ff.read()

        topmatter = get_static_file(STATIC_TOPMATTER)
        header = get_static_file(STATIC_HEADER)
        footer = get_static_file(STATIC_FOOTER)
        bottommatter = get_static_file(STATIC_BOTTOMMATTER)

        j = jinja2.Environment()
        t = j.from_string(topmatter)
        topmatter = t.render(repo=repo, meta=meta)

        j = jinja2.Environment()
        t = j.from_string(header)
        header = t.render(repo=repo, meta=meta)

        j = jinja2.Environment()
        t = j.from_string(footer)
        footer = t.render(repo=repo, meta=meta)

        html = f"""
{topmatter}
{header}
{output}
{footer}
{bottommatter}"""

    return sanic.html(html)

from . import postgresql

@app.listener("before_server_start")
async def setup_executor(app, loop):
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor())

    # give the DB some time to init
    await asyncio.sleep(5)

    app.pool = await postgresql.create_pool(os.getenv("DB_CONNECTION"))
    app.__class__.dbconn = postgresql.dbconn

    async with app.dbconn() as conn:
        sver = await postgresql.sql_1row(conn, "select version()")

        logger.info(f"Running with DB version {sver}")


if __name__ == "__main__":
    # NOTE: Sanic CLI is used in Dockerfile; thus never runs as __main__.
    app.run(host="0.0.0.0", port=1337, access_log=False, debug=True, auto_reload=True)

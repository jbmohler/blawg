import os
import tempfile
import functools
import subprocess
import asyncio
import base64
import sanic
import github
import jinja2

app = sanic.Sanic("blawg like a pro")

GITHUB_USER = "jbmohler"
GITHUB_BLOG_REPO = "testblog"

GITHUB_STATIC_DIR = "/static"
GITHUB_BLOG_DIR = "fred"


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
        print(cfile)

        raw = base64.b64decode(cfile.content)
        return raw.decode("utf8")
    except:
        print(f"did not find {static}")
        # TODO:  get more precise about exception
        return ""


@app.get("/async")
async def async_handler(request):
    await asyncio.sleep(0.1)
    return sanic.text("Done.")


@app.get("/dir/<dirpath:path>")
async def get_github_dir(request, dirpath):
    repo = get_repo()

    cfile = repo.get_contents(dirpath)

    def repr(c):
        return f"{c.type}: {c.path}"

    return sanic.text(str([repr(c) for c in cfile]))


@app.get("/rawpage/<blogpath:path>")
async def get_github_rawpage(request, blogpath):
    repo = get_repo()

    cfile = repo.get_contents(blogpath)
    raw = base64.b64decode(cfile.content)
    return sanic.text(raw.decode("utf8"))


MJ_SCRIPT = """ <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"> </script>"""


@app.get("/page/<blogpath:path>")
async def get_github_page(request, blogpath):
    repo = get_repo()

    cfile = repo.get_contents(blogpath)
    raw = base64.b64decode(cfile.content)

    with tempfile.TemporaryDirectory() as tempdir:

        iname = os.path.join(tempdir, "temp.md")
        oname = os.path.join(tempdir, "temp.html")

        with open(iname, "w") as ff:
            ff.write(raw.decode("utf8"))

        subprocess.run(["pandoc", "--mathjax", iname, "-o", oname])
        # os.system("pandoc --standalone --mathjax -f markdown -t html temp.md -o temp.html")

        with open(oname, "r") as ff:
            output = ff.read()

        topmatter = get_static_file(STATIC_TOPMATTER)
        header = get_static_file(STATIC_HEADER)
        footer = get_static_file(STATIC_FOOTER)
        bottommatter = get_static_file(STATIC_BOTTOMMATTER)

        j = jinja2.Environment()
        t = j.from_string(header)
        header = t.render(repo=repo)

        j = jinja2.Environment()
        t = j.from_string(footer)
        footer = t.render(repo=repo)

        html = f"""
{topmatter}
{header}
{output}
{footer}
{bottommatter}"""

    return sanic.html(html)


app.run(host="0.0.0.0", port=1337, access_log=False, debug=True, auto_reload=True)

import os
import tempfile
import functools
import subprocess
import asyncio
import concurrent.futures
import base64
import sanic
import github
import jinja2

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


@app.get("/index")
async def get_github_index(request):
    repo = get_repo()

    cfile = repo.get_contents(f"{GITHUB_BLOG_DIR}")

    def repr(c):
        hyper = c.path.replace(GITHUB_BLOG_DIR, "").strip("/")
        base = ""  # TODO: get this from the request header vars
        return f"<a href='{base}/page/{hyper}'>{c.name}</a><br />"

    output = "\n".join([repr(c) for c in cfile])

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


@app.get("/rawpage/<blogpath:path>")
async def get_github_rawpage(request, blogpath):
    repo = get_repo()

    cfile = repo.get_contents(blogpath)
    raw = base64.b64decode(cfile.content)
    return sanic.text(raw.decode("utf8"))


MJ_SCRIPT = """ <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"> </script>"""

# Markdown metadata
# https://stackoverflow.com/questions/44215896/markdown-metadata-format


@app.get("/page/<blogentry:path>")
async def get_github_blog_page(request, blogentry):
    repo = get_repo()

    cfile = repo.get_contents(f"{GITHUB_BLOG_DIR}/{blogentry}")
    raw = base64.b64decode(cfile.content)

    loop = asyncio.get_running_loop()

    with tempfile.TemporaryDirectory() as tempdir:
        iname = os.path.join(tempdir, "temp.md")
        oname = os.path.join(tempdir, "temp.html")

        with open(iname, "w") as ff:
            ff.write(raw.decode("utf8"))

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


@app.listener("before_server_start")
async def setup_executor(app, loop):
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1337, access_log=False, debug=True, auto_reload=True)

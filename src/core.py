import os
import re
import asyncio
import base64
import sanic
import github

app = sanic.Sanic("blawg like a pro")

GITHUB_USER = "jbmohler"
GITHUB_BLOG_REPO = "testblog"


@app.get("/async")
async def async_handler(request):
    await asyncio.sleep(0.1)
    return sanic.text("Done.")


@app.get("/rawpage/<blogpath:path>")
async def get_github_rawpage(request, blogpath):
    g = github.Github()
    repo = g.get_repo(f"{GITHUB_USER}/{GITHUB_BLOG_REPO}")

    cfile = repo.get_contents(blogpath)
    raw = base64.b64decode(cfile.content)
    return sanic.text(raw.decode("utf8"))


MJ_SCRIPT = """ <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"> </script>"""


@app.get("/page/<blogpath:path>")
async def get_github_page(request, blogpath):
    g = github.Github()
    repo = g.get_repo(f"{GITHUB_USER}/{GITHUB_BLOG_REPO}")

    cfile = repo.get_contents(blogpath)
    raw = base64.b64decode(cfile.content)

    # TODO:  use tempfile

    with open("temp.md", "w") as ff:
        ff.write(raw.decode("utf8"))

    # os.system('pandoc --mathjax temp.md -o temp.html')
    os.system("pandoc --standalone --mathjax -f markdown -t html temp.md -o temp.html")

    with open("temp.html", "r") as ff:
        output = ff.read()
        output = re.sub("<script.*mathjax.*/script>", MJ_SCRIPT, output)

    return sanic.html(output)


app.run(host="0.0.0.0", port=1337, access_log=False, debug=True)

import asyncio
import sanic
import github

app = sanic.Sanic("blawg like a pro")

GITHUB_USER = "jbmohler"
GITHUB_BLOG_REPO = "testblog"


@app.get("/async")
async def async_handler(request):
    await asyncio.sleep(0.1)
    return sanic.text("Done.")


@app.get("/page/<blogpath:path>")
async def get_github_page(request, blogpath):
    g = github.Github()
    repo = g.get_repo(f"{GITHUB_USER}/{GITHUB_BLOG_REPO}")

    text = repo.get_contents(blogpath)
    return sanic.text(text.url)


app.run(host="0.0.0.0", port=1337, access_log=False, debug=True)

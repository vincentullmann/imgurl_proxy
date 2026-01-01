"""Simple FastAPI reverse proxy app.

Forwards requests from my_domain/{domain}/{path} to https://{domain}/{path}.
"""

import fastapi
import httpx
from fastapi.responses import RedirectResponse


app = fastapi.FastAPI(title="URL Proxy Service")


def extract_target_url(path: str) -> str:
    """Extract target URL from path.

    Example: '/foo.bar/baz/qux' -> 'https://foo.bar/baz/qux'.

    """
    # Remove leading slash
    path = path.lstrip("/")

    if not path:
        raise fastapi.HTTPException(status_code=400, detail="Path cannot be empty")

    # Split by '/' to get domain and remaining path
    if "/" in path:
        domain, remaining_path = path.split("/", 1)
    else:
        domain = path
        remaining_path = ""

    if "." not in domain:
        raise ValueError("Invalid domain")

    # print(domain, remaining_path)
    # Construct target URL
    target_path = f"/{remaining_path}" if remaining_path else "/"
    target_url = f"https://{domain}{target_path}"

    # print(path, "->", target_url)
    return target_url


################################################################################


def get_full_url(path: str) -> str:
    if path.startswith("https://") or path.startswith("http://"):
        return path
    else:
        return f"https://{path}"


@app.get("/{path:path}")
async def proxy_get(request: fastapi.Request, path: str) -> fastapi.Response:
    """Proxy GET requests."""

    IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".bmp", ".tiff", ".tif", ".heic", ".heif")

    if path.endswith(IMAGE_EXTENSIONS):
        path = f"https://i.imgur.com/{path}"

    # path = get_full_url(path)

    #path = path.removeprefix("https://")
    #path = path.removeprefix("http://")
    #path = f"https://{path}"

    url = f"https://proxy.duckduckgo.com/iu/?u={path}"
    print("--------------------------------")
    print(path, "->", url)
    print("--------------------------------")

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        return fastapi.Response(content=response.content, status_code=response.status_code, headers=response.headers)
    # return await proxy_request(request, path)



async def proxy_request(request: fastapi.Request, path: str) -> fastapi.Response:
    """Handle proxying of requests to target URL."""
    # Extract target URL from path

    try:
        target_url = extract_target_url(path)
    except ValueError:
        return RedirectResponse(path)

    if "favicon" in path:
        return fastapi.Response(content="", status_code=200)

    # Get query parameters
    query_string = str(request.url.query)
    if query_string:
        target_url = f"{target_url}?{query_string}"

    # Get request body if present
    # body = None
    #' if request.method in ["POST", "PUT", "PATCH"]:
    #'     body = await request.body()

    # Forward headers (exclude host and connection)
    # headers = dict(request.headers)
    # headers.pop("host", None)
    # headers.pop("connection", None)
    # headers.pop("content-length", None)  # Let httpx calculate it


    # Make request to target URL
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(
            url=target_url,
            # headers=headers,
            # params=request.query_params,
            # cookies=request.cookies,
            # auth=request.auth,
            # content=body,
        )

    # return response
    # return "Hello, world!"

    # Get response headers (exclude some that shouldn't be forwarded)
    # response_headers = dict(response.headers)
    # response_headers.pop("content-encoding", None)  # Let FastAPI handle encoding
    # response_headers.pop("transfer-encoding", None)
    # response_headers.pop("connection", None)
    # print(response.content)

    """
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Error proxying request: {e!s}") from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}") from e
    """

    # Return response
    return fastapi.Response(
        content=response.content,
        status_code=response.status_code,
        headers=request.headers,
        # media_type=response.headers.get("content-type"),
    )


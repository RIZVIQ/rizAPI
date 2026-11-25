# RizApi

RizApi is a lightweight, synchronous Python web framework adhering to the WSGI (PEP 3333) specification. It implements custom request dispatching, parameterized route matching via format strings, global and route-specific middleware pipelines, class-based views (CBVs), and basic response abstractions.

---

## Architecture Overview

```
                      +-------------------+
                      |    WSGI Server    | (Waitress / Gunicorn)
                      +---------+---------+
                                | environ, start_response
                                v
                      +-------------------+
                      |   RizApi.__call__ |
                      +---------+---------+
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
     +---------------+                     +---------------+
     | Request(env)  |                     |  Response()   |
     +-------+-------+                     +-------+-------+
             |                                     |
             v                                     |
   [Global Middlewares]                            |
             |                                     |
             v                                     |
    [Route Matching Engine]                        |
     (parse regex patterns)                        |
             |                                     |
             v                                     |
   [Route Middlewares]                             |
             |                                     |
             v                                     v
     +---------------+                     +---------------+
     | Route Handler +-------------------->| Response.send |
     +---------------+ (updates response)  +-------+-------+
                                                   |
                                                   v
                                          Response.as_wsgi()
                                                   |
                                                   v
                                          start_response() -> [bytes]
```

### Request Lifecycle
1. **WSGI Ingestion**: An incoming HTTP request passes the WSGI `environ` dictionary and `start_response` callable to `RizApi.__call__`.
2. **Context Creation**:
   - `Request` wraps `environ`, converting environment keys to normalized snake_case object attributes and parsing query parameters.
   - `Response` initializes with fallback defaults (`404 MISSING ROUTE`, `404 NOT FOUND`).
3. **Global Middleware Pipeline**: Inbound `Request` passes through user-defined global middleware callables in registration order.
4. **Route Dispatch & Parameter Extraction**:
   - Routes are scanned sequentially against `request.path_info` using the `parse` library format engine.
   - Upon matching both path pattern and HTTP method, path parameters are extracted into keyword arguments (`**res.named`).
5. **Route Middleware Pipeline**: If matched, method-specific middlewares for that specific route are executed sequentially.
6. **Handler Invocation**: The target handler is called with `(request, response, **path_params)`. The handler mutates `response` via `.send()` or `.render()`.
7. **WSGI Serialization**: `response.as_wsgi(start_response)` invokes `start_response(status_code, headers)` and yields the encoded payload as byte chunks (`[self.text.encode()]`).

---

## Directory Structure

```
rizapi/
├── .git/                      # Git tracking directory
├── README.md                  # Project documentation and architectural specification
└── vrenv/                     # Virtual environment & framework source directory
    ├── example.py             # Sample application showing FBVs and CBVs
    ├── main.py                # Core WSGI application class (RizApi) and decorators
    ├── request.py             # WSGI environ parser and Request abstraction
    ├── response.py            # Response serialization and template rendering
    ├── pyvenv.cfg             # Virtual environment configuration
    ├── Lib/site-packages/     # Installed packages (parse, waitress, gunicorn)
    └── Scripts/               # Python and server executables
```

> **Repository Note**: The framework source files (`main.py`, `request.py`, `response.py`, `example.py`) currently reside directly inside the `vrenv/` directory in the repository tracking tree.

---

## Core Components & API Specification

### 1. Application Core (`main.py`)

#### `RizApi(middlewares=None)`
The main WSGI-compliant callable.

- **Attributes**:
  - `routes`: Dict structured as `{ "<path_pattern>": { "<HTTP_METHOD>": <handler_callable> } }`.
  - `middlewares`: List of function-type callables executed on all requests.
  - `route_specific_middleware`: Dict structured as `{ "<path_pattern>": { "<HTTP_METHOD>": [<middleware_callables>] } }`.
- **Supported Methods**: `GET`, `POST`, `DELETE`.

#### Route Decorators
- `@rizapi.get(path=None, middlewares=[])`: Registers a `GET` handler.
- `@rizapi.post(path=None, middlewares=[])`: Registers a `POST` handler.
- `@rizapi.delete(path=None, middlewares=[])`: Registers a `DELETE` handler.
- If `path` is omitted, defaults to `/{handler.__name__}`.

#### Class-Based Views (CBVs)
- `@rizapi.route(path=None, middlewares=[])`: Registers a class containing HTTP method functions.
- The decorator inspects member functions using `inspect.getmembers()` and registers functions named after supported HTTP verbs (`get`, `post`, `delete`).

---

### 2. Request Wrapper (`request.py`)

#### `Request(environ)`
Encapsulates the raw WSGI `environ` dictionary into an object interface.

- **Attribute Normalization**: Iterates through `environ` keys, replacing periods with underscores and converting to lowercase:
  ```python
  environ['PATH_INFO']      -> request.path_info
  environ['REQUEST_METHOD'] -> request.request_method
  environ['QUERY_STRING']   -> request.query_string
  ```
- **Query String Parsing**: Parses `query_string` pairs (`key=value&...`) into a `collections.defaultdict` accessible via `request.queries`.

---

### 3. Response Handler (`response.py`)

#### `Response(status_code="404 MISSING ROUTE", text="404 NOT FOUND")`
Encapsulates HTTP status codes, headers, and payload serialization.

- **Methods**:
  - `send(text="", status_code="200 OK")`: Updates response body and status code. Accepts `text` as `str` or serializable types (auto-cast via `str()`), and `status_code` as `int` or `str`.
  - `render(template_name, context={})`: Loads `{template_name}.html`, substitutes variables formatted as `{{ variable }}` using regex substitution, sets `Content-Type: text/html`, and sets status to `200 OK`.
  - `as_wsgi(start_response)`: Executes the WSGI callback `start_response(self.status_code, headers=self.headers)` and returns `[self.text.encode()]`.

---

## Usage Examples

### Function-Based Views & Parameterized Routes

```python
from main import RizApi

app = RizApi()

# Basic GET route with auto-generated path "/health"
@app.get()
def health(req, res):
    res.send({"status": "healthy"}, status_code=200)

# Explicit POST route returning list data
@app.post("/items")
def create_item(req, res):
    res.send(["created", "item_01"], status_code=201)

# Dynamic URL matching with named parameters
@app.get("/users/{user_id}")
def get_user(req, res, user_id):
    # Path parameter 'user_id' is passed as a keyword argument
    res.send(f"User ID: {user_id}", status_code=200)
```

### Class-Based Views

```python
from main import RizApi

app = RizApi()

@app.route("/users")
class UserResource:
    def get(req, res):
        limit = req.queries.get("limit", "10")
        res.send(f"Fetching users (limit={limit})", 200)

    def post(req, res):
        res.send("User created", 201)

    def delete(req, res):
        res.send("User deleted", 204)
```

### Global and Route-Specific Middleware

Middlewares are functions that receive the `request` object and can inspect or modify it before handlers execute:

```python
from main import RizApi

def log_request(req):
    print(f"[{req.request_method}] {req.path_info}")

def authenticate(req):
    token = getattr(req, "http_authorization", None)
    if not token:
        print("Unauthorized request attempt")

# Attach global middleware
app = RizApi(middlewares=[log_request])

# Attach route-specific middleware
@app.get("/secure/data", middlewares=[authenticate])
def secure_data(req, res):
    res.send("Confidential payload", 200)
```

---

## Deployment & Running

Because `RizApi` exposes a standard WSGI application callable (`__call__(environ, start_response)`), it can be run on any WSGI server.

### Windows (using Waitress)

From the project root:

```powershell
.\vrenv\Scripts\waitress-serve --listen=127.0.0.1:8000 --app-dir=vrenv example:rizapi
```

Or navigating into `vrenv/`:

```powershell
cd vrenv
..\vrenv\Scripts\waitress-serve --listen=127.0.0.1:8000 example:rizapi
```

### Linux / POSIX (using Gunicorn)

```bash
gunicorn -w 4 -b 127.0.0.1:8000 --chdir vrenv example:rizapi
```

---

## Technical Notes & Implementation Characteristics

1. **Route Resolution Complexity**: Route matching uses sequential iteration over registered route patterns with `parse(pattern, request.path_info)`. Route lookup is $O(N)$ with respect to registered routes rather than $O(1)$ tree/hash lookups.
2. **Synchronous Execution**: All middleware, handlers, and I/O operations are synchronous and blocking. Concurrency depends on the WSGI server worker model (multi-process or thread pool).
3. **Environ Key Normalization**: The request layer maps any environment key containing `.` to `_`. For example, server-specific metadata like `wsgi.url_scheme` is accessed via `request.wsgi_url_scheme`.
4. **Query String Splitting**: `Request.__init__` splits query strings using basic string partitioning on `&` and `=`. Complex query patterns (duplicate keys, unencoded values, lists) are not handled by default; only the last key-value pair is retained in `self.queries`.
5. **Template Renderer**: The `Response.render` method uses basic regular expressions for placeholder replacement (`{{\s*key\s*}}`). Production applications should migrate to a dedicated engine like Jinja2 if conditional logic, loops, or template inheritance are required.

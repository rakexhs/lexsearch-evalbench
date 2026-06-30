# Building APIs with FastAPI

<!-- category: web-frameworks -->

## Path operations
FastAPI uses Python type hints to define request and response models. A path
operation is declared with a decorator such as `@app.get("/items/{item_id}")`. Path
parameters are taken from the URL, while query parameters are function arguments
that are not part of the path.

## Validation with Pydantic
Request bodies are declared as Pydantic models. FastAPI automatically validates
incoming JSON against the model and returns a 422 Unprocessable Entity response with
a detailed error list when validation fails.

## Automatic docs
FastAPI generates interactive API documentation automatically. Swagger UI is served
at `/docs` and ReDoc at `/redoc`, both derived from the OpenAPI schema that FastAPI
produces from your type hints.

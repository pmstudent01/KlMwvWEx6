# Vehicle Service API

A Python [FastAPI](https://fastapi.tiangolo.com/) implementation of the
**Vehicle Service Collection**. Responses, status codes, validation and error
messages mirror the examples saved in the Postman collection.

## Endpoints

| Method | Path             | Description        | Status codes        |
|--------|------------------|--------------------|---------------------|
| POST   | `/vehicles`      | Create a vehicle   | 201, 400, 409       |
| GET    | `/vehicles/{id}` | Retrieve a vehicle | 200, 404            |
| PATCH  | `/vehicles/{id}` | Update a vehicle   | 200, 400, 404, 409  |
| DELETE | `/vehicles/{id}` | Delete a vehicle   | 204, 404            |

A seed vehicle with `id: 1` ("The Lisa Marie") is loaded on startup, so
`GET /vehicles/1` works immediately. Data is held in memory and resets on
restart.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API base URL: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

## Example requests

```bash
# Create a vehicle
curl -X POST http://localhost:8000/vehicles \
  -H "Content-Type: application/json" \
  -d '{"nickName":"Dolly","vin":"JN8AZ2KR1AT169594","make":"Nissan","model":"Cube","year":"2010","miles":59000}'

# Retrieve it
curl http://localhost:8000/vehicles/1

# Update mileage
curl -X PATCH http://localhost:8000/vehicles/1 \
  -H "Content-Type: application/json" \
  -d '{"miles":160000}'

# Delete it
curl -X DELETE http://localhost:8000/vehicles/1
```

## Point Postman at this app

Set the `baseUrl` environment variable to `http://localhost:8000`, then run
the **Vehicle Service Collection** requests against your local app.

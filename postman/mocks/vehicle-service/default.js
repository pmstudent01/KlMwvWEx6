const http = require('http');
const PORT = process.env.PORT || 4500;
const STATE_KEY = 'vehicle-service:vehicles';

const seed = [{
  id: 1,
  nickName: 'The Lisa Marie',
  vin: '4M2DV11W4RDJ53329',
  make: 'Mercury',
  model: 'Villager',
  year: '1994',
  miles: 159864
}];

function send(res, status, body) {
  const headers = body === undefined ? {} : { 'Content-Type': 'application/json' };
  res.writeHead(status, headers);
  res.end(body === undefined ? '' : JSON.stringify(body));
}

async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  let raw = '';
  for await (const chunk of req) raw += chunk;
  if (!raw) return {};
  return JSON.parse(raw);
}

async function getVehicles() {
  let vehicles = await pm.state.get(STATE_KEY);
  if (!Array.isArray(vehicles)) {
    vehicles = seed;
    await pm.state.set(STATE_KEY, vehicles);
  }
  return vehicles;
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    const match = url.pathname.match(/^\/vehicles\/(\d+)$/);

    // @endpoint POST /vehicles
    if (req.method === 'POST' && url.pathname === '/vehicles') {
      const body = await readBody(req);
      const required = ['nickName', 'vin', 'make', 'model', 'year', 'miles'];
      const missing = required.find((key) => body[key] === undefined || body[key] === '');
      if (missing) return send(res, 400, { message: `Request body missing required attribute: ${missing}` });

      const vehicles = await getVehicles();
      const duplicate = vehicles.find((vehicle) => vehicle.vin === body.vin);
      if (duplicate) {
        return send(res, 409, {
          message: `Vehicle with VIN ${body.vin} already exists. Existing vehicle ID: ${duplicate.id}`
        });
      }

      const id = vehicles.reduce((max, vehicle) => Math.max(max, vehicle.id), 0) + 1;
      const vehicle = { id, ...body };
      vehicles.push(vehicle);
      await pm.state.set(STATE_KEY, vehicles);
      return send(res, 201, vehicle);
    }

    // @endpoint GET /vehicles/:id
    if (req.method === 'GET' && match) {
      const id = Number(match[1]);
      const vehicles = await getVehicles();
      const vehicle = vehicles.find((item) => item.id === id);
      return vehicle
        ? send(res, 200, vehicle)
        : send(res, 404, { message: `Vehicle with id: ${id} not found.` });
    }

    // @endpoint PATCH /vehicles/:id
    if (req.method === 'PATCH' && match) {
      const id = Number(match[1]);
      const body = await readBody(req);
      const vehicles = await getVehicles();
      const index = vehicles.findIndex((item) => item.id === id);
      if (index < 0) return send(res, 404, { message: `Vehicle with id: ${id} not found.` });
      if (!body || Array.isArray(body) || typeof body !== 'object' || Object.keys(body).length === 0) {
        return send(res, 400, { message: 'Bad request body.' });
      }
      const duplicate = vehicles.find((item) => item.vin === body.vin && item.id !== id);
      if (duplicate) return send(res, 409, { message: `Vehicle with VIN ${body.vin} already exists. Existing vehicle ID: ${duplicate.id}` });

      vehicles[index] = { ...vehicles[index], ...body, id };
      await pm.state.set(STATE_KEY, vehicles);
      return send(res, 200, vehicles[index]);
    }

    // @endpoint DELETE /vehicles/:id
    if (req.method === 'DELETE' && match) {
      const id = Number(match[1]);
      const vehicles = await getVehicles();
      const index = vehicles.findIndex((item) => item.id === id);
      if (index < 0) return send(res, 404, { message: `Vehicle with id: ${id} not found.` });
      vehicles.splice(index, 1);
      await pm.state.set(STATE_KEY, vehicles);
      return send(res, 204);
    }

    return send(res, 404, { error: 'Mock route not defined', method: req.method, path: url.pathname });
  } catch (error) {
    return send(res, 400, { message: error.message });
  }
});

server.listen(PORT);

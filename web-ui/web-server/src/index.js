/*
'use strict';

const api = require('./app');
const port = api.get('port');
const feathers = require('feathers');
const express = require('express');

api.use(api.logger.expressLogger);

api.logger.info('Logging...');

process.on('unhandledRejection', (reason, p) => {
  console.log("Unhandled Rejection at: Promise ", p, " reason: ", reason);
});

const app = express();

app.use('/multiscan/webui', api);
console.log(port)
const server = app.listen(port);
console.log(server)
// const server = app.listen(port);
api.setup(server);

server.on('listening', () =>
  console.log(`Feathers application started on ${api.get('host')}:${port}`)
);
*/

///*
'use strict';

const app = require('./app');
const port = app.get('port');
const server = app.listen(port);

app.use(app.logger.expressLogger);

app.logger.info('Logging...');

process.on('unhandledRejection', (reason, p) => {
  console.log("Unhandled Rejection at: Promise ", p, " reason: ", reason);
});

server.on('listening', () =>
  console.log(`Feathers application started on ${app.get('host')}:${port}`)
);
//*/
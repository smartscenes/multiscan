const winston = require('winston');
const expressWinston = require('express-winston');
const WinstonContext = require('winston-context');

const expressLogger = expressWinston.logger({
  transports: [
    new (winston.transports.File)({ filename: 'logs/express.log' })
  ],
  meta: true, // optional: control whether you want to log the meta data about the request (default to true)
  msg: 'HTTP {{res.statusCode}} {{req.method}} {{res.responseTime}}ms {{req.url}}', // optional: customize the default logging message.
  //expressFormat: true, // Use the default Express/morgan request formatting, with the same colors. Enabling this will override any msg and colorStatus if true. Will only output colors on transports with colorize set to true
  //colorStatus: true, // Color the status code, using the Express/morgan color palette (default green, 3XX cyan, 4XX yellow, 5XX red). Will not be recognized if expressFormat is true
  //ignoreRoute: function (req, res) { return false; } // optional: allows to skip some log messages based on request and/or response
});

const defaultLogger = winston.createLogger({
  level: 'info',
  transports: [
    new (winston.transports.Console)({handleExceptions: true}),
    new (winston.transports.File)({ filename: 'logs/server.log', handleExceptions: true })
  ],
  exitOnError: false
});
// winston.add(winston.transports.File, {
//   filename: 'logs/server.log',
//   handleExceptions: true
// });
// winston.exitOnError = false;

const Logger = function(name, meta) {
  const logger = winston.loggers.get(name) || defaultLogger;
  meta = meta || {};
  if (logger === winston && !meta.name) { meta.name = name; }
  const ctx = new WinstonContext(logger, '', meta);
  ctx.expressLogger = expressLogger;
  return ctx;
};

module.exports = Logger;

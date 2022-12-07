// Using the simplest possible proxying for proxying data located on servers
const csv = require('csv');
const errors = require('feathers-errors');
const _ = require('lodash');
const feathers = require('feathers');
// const api = require('./app');

module.exports = function() {
  const app = this;

  const scanService = app.service('/api/scans');
  const scanmetaService = app.service('/api/scanmeta');

  function groupByArrayField(data, field) {
    groupedByField = {};
    for (let i = 0; i < data.length; i++) {
      const d = data[i];
      const values = d[field];
      if (values) {
        for (let j = 0; j < values.length; j++) {
          const v = values[j];
          if (v != undefined) {
            if (groupedByField[v]) {
              groupedByField[v].push(d);
            } else {
              groupedByField[v] = [d];
            }
          }
        }
      }
    }
    return groupedByField;
  }

  // render home page
  //app.get('/', (req, res) => res.render('index'));

  // render annotations
  app.get('/scans/annotations', (req, res, next) => {
    res.render('annotations', {
      settings: app.get('settings')
    });
  });

  // render scans by devices
  app.get('/scans/devices-id', (req, res, next) => {
    scanService.find({query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByDeviceId = _.groupBy(scans.filter( (x) => {return x.deviceId;}), 'deviceId');
      } else {
        scansByDeviceId = {};
      }
      const devices = _.map(scansByDeviceId, (deviceScans, deviceId) => {
        let deviceNames = _.map(deviceScans, (scan) => { return scan.deviceName; });
        deviceNames = _.uniq(_.filter(deviceNames, (name) => { return name; }));
        return { id: deviceId, names: deviceNames, scans: deviceScans };
      });
      res.render('devicesById', {
        devices: devices,
        settings: app.get('settings')
      });
    }).catch(next);
  });


  // render scans by device ids (for new web)
  app.get('/api/stats/device_ids', (req, res, next) => {
    scanService.find({query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByDeviceId = _.groupBy(scans.filter( (x) => {return x.deviceId;}), 'deviceId');
      } else {
        scansByDeviceId = {};
      }
      const devices = _.map(scansByDeviceId, (deviceScans, deviceId) => {
        let deviceNames = _.map(deviceScans, (scan) => { return scan.deviceName; });
        deviceNames = _.uniq(_.filter(deviceNames, (name) => { return name; }));
        return { id: deviceId, names: deviceNames, scans: deviceScans.length };
      });
      res.json(devices);
    }).catch(next);
  });

  app.get('/scans/devices-name', (req, res, next) => {
    scanService.find({query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByDeviceName = _.groupBy(scans.filter( (x) => {return x.deviceName;}), 'deviceName');
      } else {
        scansByDeviceName = {};
      }
      const devices = _.map(scansByDeviceName, (deviceScans, deviceName) => {
        let deviceIds = _.map(deviceScans, (scan) => { return scan.deviceId; });
        deviceIds = _.uniq(_.filter(deviceIds, (id) => { return id; }));
        return { name: deviceName, ids: deviceIds, scans: deviceScans };
      });
      res.render('devicesByName', {
        devices: devices,
        settings: app.get('settings')
      });
    }).catch(next);
  });

  // render segmentation results by scan id
  app.get('/scans/segs', (req, res, next) => {
    //res.render('manage');
    scanService.find({ id: { '$ne': null }, query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansById = _.groupBy(scans.filter( (x) => {return x.id;}), 'id');
      } else {
        scansById = {};
      }
      const scenes = _.map(scansById, (groupedScans, name) => {
        let sceneTypes = _.map(groupedScans, (scan) => { return scan.sceneType; });
        sceneTypes = _.uniq(_.filter(sceneTypes, (sceneType) => { return sceneType; }));
        return { name: name, type: sceneTypes, scans: groupedScans };
      });
      res.render('segmentation', {
        scenes: scenes,
        settings: app.get('settings')
      });
    }).catch(next);
  });

  // render scans by sceneName
  app.get('/scans/scenes', (req, res, next) => {
    //res.render('manage');
    scanService.find({ sceneName: { '$ne': null }, query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByScene = _.groupBy(scans.filter( (x) => {return x.sceneName;}), 'sceneName');
      } else {
        scansByScene = {};
      }
      const scenes = _.map(scansByScene, (groupedScans, name) => {
        let sceneTypes = _.map(groupedScans, (scan) => { return scan.sceneType; });
        sceneTypes = _.uniq(_.filter(sceneTypes, (sceneType) => { return sceneType; }));
        return { name: name, type: sceneTypes, scans: groupedScans };
      });
      res.render('scenes', {
        scenes: scenes,
        settings: app.get('settings')
      });
    }).catch(next);
  });

  // render scans by sceneName (for new web)
  app.get('/api/stats/scenes_names', (req, res, next) => {
    //res.render('manage');
    scanService.find({ sceneName: { '$ne': null }, query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByScene = _.groupBy(scans.filter( (x) => {return x.sceneName;}), 'sceneName');
      } else {
        scansByScene = {};
      }
      const scenes = _.map(scansByScene, (groupedScans, name) => {
        let sceneTypes = _.map(groupedScans, (scan) => { return scan.sceneType; });
        sceneTypes = _.uniq(_.filter(sceneTypes, (sceneType) => { return sceneType; }));
        return { name: name, type: sceneTypes, scans: groupedScans.length };
      });
      res.json(scenes);
    }).catch(next);
  });

  // render scans by sceneType
  app.get('/scans/scenes-type', (req, res, next) => {
    if (!req.query['group']) {
      req.query['group'] = { '$ne': 'nyuv2' };
    }
    scanService.find({query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByScene = _.groupBy(scans.filter( (x) => {return x.sceneType;}), 'sceneType');
      } else {
        scansByScene = {};
      }
      const scenes = _.map(scansByScene, (groupedScans, type) => {
        const byName = _.groupBy(groupedScans.filter( (x) => {return x.sceneName;}), 'sceneName');
        return { type: type, scans: groupedScans, numScenes: _.size(byName) };
      });
      res.render('scenesByType', {
        scenes: scenes,
        settings: app.get('settings')
      });
    }).catch(next);
  });

  // render scans by sceneType (for new web)
  app.get('/api/stats/scenes_types', (req, res, next) => {
    if (!req.query['group']) {
      req.query['group'] = { '$ne': 'nyuv2' };
    }
    scanService.find({query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByScene = _.groupBy(scans.filter( (x) => {return x.sceneType;}), 'sceneType');
      } else {
        scansByScene = {};
      }
      const scenes = _.map(scansByScene, (groupedScans, type) => {
        return { type: type, scans: groupedScans.length};
      });
      res.json(scenes);
    }).catch(next);
  });

  // render scans by user
  app.get('/scans/users', (req, res, next) => {
    scanService.find({ userName: { '$ne': null }, query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByUser = _.groupBy(scans.filter( (x) => {return x.userName;}), 'userName');
      } else {
        scansByUser = {};
      }
      const users = _.map(scansByUser, (groupedScans, name) => {
        return { name: name, scans: groupedScans };
      });
      res.render('users', {
        users: users,
        settings: app.get('settings')
      });
    }).catch(next);
  });

  // render scans by user (for new web)
  app.get('/api/stats/users', (req, res, next) => {
    scanService.find({ userName: { '$ne': null }, query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByUser = _.groupBy(scans.filter( (x) => {return x.userName;}), 'userName');
      } else {
        scansByUser = {};
      }
      const users = _.map(scansByUser, (groupedScans, name) => {
        return { name: name, scans: groupedScans.length };
      });
      res.json(users);
    }).catch(next);
  });

  // render scans by tag
  app.get('/scans/tags', (req, res, next) => {
    scanService.find({ tag: { '$ne': null }, query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByTag = groupByArrayField(scans, 'tags');
      } else {
        scansByTag = {};
      }
      const tags = _.map(scansByTag, (groupedScans, name) => {
        return { name: name, scans: groupedScans };
      });
      res.render('tags', {
        tags: tags,
        settings: app.get('settings')
      });
    }).catch(next);
  });

  // render scans by tag (for new web)
  app.get('/api/stats/tags', (req, res, next) => {
    scanService.find({ tag: { '$ne': null }, query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        scansByTag = groupByArrayField(scans, 'tags');
      } else {
        scansByTag = {};
      }
      const tags = _.map(scansByTag, (groupedScans, name) => {
        return { name: name, scans: groupedScans.length };
      });
      res.json(tags);
    }).catch(next);
  });

  // render our list of messages retrieving them from our service
  app.get('/scans/browse', (req, res, next) => {
    res.render('browse');
  });

  app.get('/scans/list', (req, res, next) => {
    const queued = app.process_queue.list();
    const queuedById = _.keyBy(queued, 'id');
    scanService.find({query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        for (let i = 0; i < scans.length; i++) {
          const scan = scans[i];
          const queueState = queuedById[scan['id']];
          if (queueState) {
            scan.queueState = { queued: true, running: !!queueState.lock };
          }
        }
      }
      // Hacky way to get count of total total
      result.data = scans;
      scanService.find({query: {'$limit': 1}}).then( all => {
        result.totalAll = all.total;
        res.json(result);
      }).catch(next);
    }).catch(next);
  });

  // app.get('/scans/browse/nyu', (req, res, next) => {
  //   req.query['group'] = 'nyuv2';
  //   scanService.find({query: req.query}).then(result => {
  //     const scans = result.data ? result.data : result;
  //     res.render('manage', {
  //       scans: scans, total: result.total,
  //       settings: app.get('settings'),
  //       nyu: true
  //     });
  //   }).catch(next);
  // });

  // app.get('/scans/browse/nyu/frames', (req, res, next) => {
  //   res.render('nyuframes', {
  //     settings: app.get('settings')
  //   });
  // });

  app.get('/scans/manage', (req, res, next) => {
    //res.render('manage');
    if (!req.query['$sort']) {
      req.query['$sort'] = { 'createdAt': -1 };
    }
    if (!req.query['group']) {
      req.query['group'] = { '$ne': 'nyuv2' };
    }
    //console.log(req.query);
    const queued = app.process_queue.list();
    const queuedById = _.keyBy(queued, 'id');
    scanService.find({query: req.query}).then(result => {
      // This handles paginated and non-paginated services
      const scans = result.data ? result.data : result;
      if (scans && scans.length) {
        for (let i = 0; i < scans.length; i++) {
          const scan = scans[i];
          const queueState = queuedById[scan['id']];
          if (queueState) {
            scan.queueState = { queued: true, running: !!queueState.lock };
          }
        }
      }
      res.render('manage', {
        scans: scans, total: result.total,
        processQueue: app.process_queue.status(),
        manageView: true,
        settings: app.get('settings')
      });
    }).catch(next);
  });

  app.get('/scans/process/:scanId', (req, res, next) => {
    app.process_queue.push( { id: req.params.scanId });
    res.json({ status: 'ok', size: app.process_queue.size() });
  });

  app.get('/scans/process', (req, res, next) => {
    const queued = app.process_queue.list();
    scanService.find({}).then(result => {
      // TODO: Filter by the ones that are on the process queue
      const scans = result.data ? result.data : result;
      const scansById = _.keyBy(scans, 'id');
      const queuedScans = queued.map( queueState => {
        const scanId = queueState.id;
        const scan = scansById[scanId];
        if (!scan) {
          scan = {
            id: scanId
          };
        }
        scan.queueState = { queued: true, running: !!queueState.lock };
        return scan;
      });
      res.render('manage', {
        scans: queuedScans,
        total: queued.length,
        processQueue: app.process_queue.status(),
        processView: true,
        settings: app.get('settings')
      });
    }).catch(next);
  });


  app.post('/scans/edit', (req, res, next) => {
    const logger = app.logger.getContext('', { path: '/scans/edit'});
    const params = req.body;
    logger.info('Processing ' + JSON.stringify(params));
    if (params.action === 'edit') {
      if (!params.data) {
        throw new errors.GeneralError(
          { message: 'No data for /scans/edit: ' + params.action });
      }
      // Editing
      //const patchData = _.map(params.data, function(v,k) { v._id = k; return v; });
      //console.log(patchData);
      // TODO: Handle multple rows being editted
      _.each(params.data, function(v,k) {
        scanmetaService.patch(k, v, { nedb: { upsert: true } }).then(result => {
          scanService.patch(k, v).then(scanResult => {
            if (!_.isArray(scanResult)) {
              scanResult = [scanResult];
            }
            _.each(result, function(f) {
              f.id = f._id;
              delete f.files;
              delete f._id;
            });
            res.json({ status: 'ok', data: scanResult });
          }).catch(next);
        }).catch(next);
      });
    } else {
      throw new errors.GeneralError(
          { message: 'Unsupported action for /scans/edit: ' + params.action });
    }
  });


  // TODO: Move logic into service
  // custom population of scans from csv
  app.post('/scans/populate', (req, res, next) => {
    const logger = app.logger.getContext('', { path: '/scans/populate'});
    const preserveKeys = ['sceneName', 'sceneType'];
    function error(e) {
      console.log(e);
      logger.error(e);
      res.json(new errors.GeneralError(
        { message: 'Error processing /scans/populate', error: e }));
    }

    function populate(data) {
      logger.info('Populating ' + data.length + ' scans');
      scanService.create(data).then( result => {
        scanService.find().then( found => {
          //console.log(found);
          res.json({ status: 'ok', processed: result.length, total: found.total });
        }).catch(error);
      }).catch(error);
    }

    function normalizeValue(v) {
      if (typeof v === 'string') {
        const vl = v.toLowerCase();
        if (vl === 'true') {
          return true;
        } else if (vl === 'false') {
          return false;
        }
      }
      return v;
    }

    function normalizeObject(obj) {
      for (k in obj) {
        if (obj.hasOwnProperty(k)) {
          obj[k] = normalizeValue(obj[k]);
        }
      }
    }

    function populateAll(err, data) {
      //console.log(data);
      if (data) {
        if (!_.isArray(data)) {
          data = _.values(data);
        }
        logger.info('Processing /scans/populate for ' + data.length + ' scans');
        for (let i = 0; i < data.length; i++) {
           normalizeObject[data[i]];
           if (data[i].path) {
              let subgroup = data[i].path.replace(data[i].id, '');
              subgroup = _.trim(subgroup, '/\\');
              if (subgroup) {
                data[i].subgroup = subgroup;
              }
           }
           data[i]._orig = _.pick(data, preserveKeys);
           data[i]._id = data[i].id;
        }
        if (req.query.group) {
          for (let i = 0; i < data.length; i++) {
            data[i].group = req.query.group;
            console.log(req.query.group);
          }
        }

        function replaceAndPopulate() {
          if (req.query.replace) {
            // Replace all
            if (req.query.replace == 'group' && req.query.group) {
              logger.info('Remove group ' + req.query.group);
              scanService.remove(null, {query: {group: req.query.group}} ).then( result => {
                populate(data);
              }).catch(error);
            } else if (req.query.replace == 'all') {
              logger.info('Remove all');
              scanService.remove(null, {}).then( result => {
                populate(data);
              }).catch(error);
            } else {
              logger.info('Remove individual scans');
              const ids = data.map( x => x.id );
              scanService.remove(null, {query: {id: { $in: ids }} }).then( result => {
                populate(data);
              }).catch(error);
            }
          } else {
            populate(data);
          }
        }

        scanmetaService.find({}).then( metaResults => {
          // combine data and metaResults
          if (metaResults.data) {
            const metaById = _.keyBy(metaResults.data, '_id');
            for (let i = 0; i < data.length; i++) {
              const meta = metaById[data[i].id];
              if (meta) {
                _.assign(data[i], meta);
              }
            }
          }

          replaceAndPopulate();
        }).catch(error);
      } else {
        if (err) {
          logger.error(err);
        } else {
          logger.error('No data');
        }
        res.json(new errors.GeneralError(
          { message: 'Error processing /scans/populate: ' + err }));
      }
    }

    if (typeof req.body === 'string') {
      // Convert from csv to json
      csv.parse(req.body, { skip_empty_lines: true, columns: true }, populateAll);
    } else {
      populateAll(null, req.body);
    }
  });

};

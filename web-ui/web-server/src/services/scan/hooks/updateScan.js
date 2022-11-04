"use strict";

// src/services/scan/hooks/updateScan.js
//
// Use this hook to manipulate incoming or outgoing data.
// For more information on hooks see: http://docs.feathersjs.com/hooks/readme.html

const defaults = {};

module.exports = function (options) {
  options = Object.assign({}, defaults, options);

  return function (hook) {
    var settings = hook.app.get("settings");

    function updateScan(scan) {
      let group = "staging";
      if (group === "nyuv2") {
        scan.modelId = group + "." + scan.id;
      } else {
        scan.modelId = "scan-" + group + "." + scan.id;
      }
      if (scan.numColorFrames == undefined) {
        scan.numColorFrames = scan.numTransforms;
      }
      if (scan.numColorFrames > 0) {
        scan.scanSecs = scan.numColorFrames / 30;
      }
      if (scan.floorAreaFilled > 0 && scan.floorArea > 0) {
        scan.floorAreaRatio = scan.floorArea / scan.floorAreaFilled;
      }

      var rootPath =
        settings.scansPaths[group] ||
        settings.scansPaths["default"] + "/" + group;
      var scanPath = rootPath + "/" + scan.path + "/";
      if (scan.files) {
        for (var i = 0; i < scan.files.length; i++) {
          var f = scan.files[i];
          if (f.name === scan.id + "_thumb.jpg") {
            scan.videoThumbnailUrl = scanPath + f.name;
          } else if (f.name === scan.id + "_preview.mp4") {
            scan.videoMp4Url = scanPath + f.name;
          }
        }
      }

      if (scan.hasThumbnail) {
        scan.previewUrl = scanPath + scan.id + "_ply_thumb_low.png";
      }
      if (scan.hasObjThumbnail) {
        scan.previewUrl = scanPath + scan.id + "_obj_thumb_low.png";
      }
      if (scan.hasObjThumbnailMVS) {
        scan.previewUrl = scanPath + settings.outputs + "/" + scan.id + "_obj_thumb_low.png";
      }

      scan.alignmentThumbnail = scanPath + settings.outputs + "/" + scan.id + "_postalign.png";
    }

    const isPaginated = hook.method === "find" && hook.result.data;
    const data = isPaginated ? hook.result.data : hook.result;

    if (Array.isArray(data)) {
      data.forEach((scan) => updateScan(scan));
    } else {
      updateScan(data);
    }
    hook.updateScan = true;
  };
};

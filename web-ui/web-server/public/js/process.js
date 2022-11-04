function ProcessQueue(url) {
  this.url = url;
  this.__downloader = new Downloader();
}

ProcessQueue.prototype.__submitAndRun = function (name, path, data, onSuccess) {
  path = path || name;
  $.ajax({ url: path[0] === "/" ? path : this.url + path, data: data })
    .done(function (resp) {
      console.log("%s(%s) success", name, data ? JSON.stringify(data) : "");
      onSuccess(resp);
    })
    .fail(function () {
      console.log("%s(%s) error", name, data ? JSON.stringify(data) : "");
    });
};

ProcessQueue.prototype.__submitAndReload = function (name, path, data) {
  this.__submitAndRun(name, path, data, function () {
    location.reload();
  });
};

ProcessQueue.prototype.__downloadFiles = function (scanId, scanPath, exts) {
  var self = this;
  this.__submitAndRun(
    "download",
    "../../api/scans/" + scanId,
    null,
    function (scan) {
      console.log(scan);
      if (scan.files && scan.files.length > 0) {
        var files = scan.files;
        if (exts) {
          var fexts = exts.map(function (ext) {
            return scanId + ext;
          });
          files = files.filter(function (file) {
            return fexts.indexOf(file.name) >= 0;
          });
        }
        var base = settings.scanFilesPath + "/";
        var urls = files.map(function (file) {
          return base + scanId + "/" + file.name;
        });
        self.__downloader.download(urls);
      } else {
        bootbox.alert("No files to download for scan " + scanId);
      }
    }
  );
};

ProcessQueue.prototype.initCancelButton = function (button, running) {
  var self = this;
  if (button) {
    button.off("click");
    if (running) {
      button.attr("class", "btn btn-danger cancelBtn");
    } else {
      button.attr("class", "btn btn-warning cancelBtn");
    }
    button.text("Cancel");
    button.attr("title", "Remove from process queue");
    button.click(function () {
      self.remove($(this).attr("data-id"), $(this));
    });
  }
};

ProcessQueue.prototype.initAddButton = function (button) {
  var self = this;
  if (button) {
    button.off("click");
    button.attr("class", "btn btn-primary cancelBtn");
    button.text("Process");
    button.attr("title", "Add to process queue");
    button.click(function () {
      self.add($(this).attr("data-id"), $(this));
    });
  }
};

const custom_actions = [
  "convert",
  "recons",
  "texturing",
  "photogrammetry",
  "knownposes",
  "segmentation",
  "render",
  "thumbnail",
  "clean",
  "alignpairs",
];

ProcessQueue.prototype.__trigger_process = function (scanId, actions, url, button) {
  var self = this;
  $.ajax({ type: "POST", url: url + 'add', data: { scanId: scanId, "overwrite": 1, "actions": JSON.stringify(actions) } })
    .done(function(resp) {
      console.log('add %s success', scanId, resp);
      self.initCancelButton(button, resp.ticket.isStarted);
    })
    .fail(function () {
      console.log("add %s error", scanId);
    });
}

ProcessQueue.prototype.add = function (scanId, button) {
  var self = this;
  var actions = [];
  for (var action_name of custom_actions) {
    var checked = $(
      `input:checkbox[name=${action_name}][data-id=${scanId}]`
    ).is(":checked");
    if (checked) {
      actions.push(action_name);
    }
  }

  var process_url = this.url;

  // check if the scanID is tag
  var re = new RegExp("scene_+");
  if (re.test(scanId)) {
    $.getJSON('../scans/list', function(data) {
        let scan_list = data.data;
        for (const scan of scan_list) {
          if (scan.sceneName) {
            let scene_name = scan.sceneName;
            if (scanId.replace('scene_', '') === scene_name) {
              // console.log(scan);
              self.__trigger_process(scan.id, actions, process_url, button);
            }
          }
        }
      }
    );
  }
  else {
    self.__trigger_process(scanId, actions, process_url, button);
  }
};

ProcessQueue.prototype.remove = function (scanId, button) {
  var self = this;
  $.ajax({ url: this.url + "remove", data: { scanId: scanId } })
    .done(function (resp) {
      console.log("remove %s success", scanId);
      self.initAddButton(button);
    })
    .fail(function () {
      console.log("remove %s error", scanId);
    });
};

ProcessQueue.prototype.initProcessButtons = function (div) {
  var self = this;
  // $(div).find('.processBars').clear();
  // $(div).find('.processBars').each( function() {

  // });

  $(div).find(".processBtn").off("click");
  $(div)
    .find(".processBtn")
    .click(function () {
      self.add($(this).attr("data-id"), $(this));
    });

  $(div).find(".cancelBtn").off("click");
  $(div)
    .find(".cancelBtn")
    .click(function () {
      self.remove($(this).attr("data-id"), $(this));
    });

  $(div).find(".moveTopBtn").off("click");
  $(div)
    .find(".moveTopBtn")
    .click(function () {
      self.__submitAndReload("move top", "add", {
        scanId: $(this).attr("data-id"),
        priority: "max",
      });
    });

  $(div).find(".moveBottomBtn").off("click");
  $(div)
    .find(".moveBottomBtn")
    .click(function () {
      self.__submitAndReload("move bottom", "add", {
        scanId: $(this).attr("data-id"),
        priority: "min",
      });
    });

  if (self.__downloader) {
    $(div).find(".downloadAllBtn").off("click");
    $(div)
      .find(".downloadAllBtn")
      .click(function () {
        var scanId = $(this).attr("data-id");
        var scanPath = $(this).attr("data-path");
        self.__downloadFiles(scanId, scanPath);
      });

    $(div).find(".downloadRawBtn").off("click");
    $(div)
      .find(".downloadRawBtn")
      .click(function () {
        var scanId = $(this).attr("data-id");
        var scanPath = $(this).attr("data-path");
        self.__downloadFiles(scanId, scanPath, [
          ".json",
          ".jsonl",
          ".mp4",
          ".confidence.zlib",
          ".depth.zlib",
        ]);
      });
  }
};

ProcessQueue.prototype.initBasicButtons = function () {
  var self = this;
  $("#clearProgressQueueBtn").click(function () {
    bootbox.confirm(
      "Are you sure you want to clear the process queue?",
      function (result) {
        if (result) {
          self.__submitAndReload("clear");
        }
      }
    );
  });
  $("#pauseResumeBtn").click(function () {
    var btn = $(this);
    var action = btn.data("action");
    if (action === "pause" || action === "resume") {
      self.__submitAndRun(action, action, undefined, function (resp) {
        console.log(resp);
        if (resp.isPaused) {
          btn
            .data("action", "resume")
            .removeClass("btn-warning")
            .addClass("btn-success")
            .text("Resume");
        } else {
          btn
            .data("action", "pause")
            .removeClass("btn-success")
            .addClass("btn-warning")
            .text("Pause");
        }
      });
    } else {
      console.warning("Unsupported action: " + action);
    }
  });
  $("#reindexBtn").click(function () {
    bootbox.confirm("Are you sure you want to reindex?", function (result) {
      if (result) {
        self.__submitAndReload("reindex", "../../scans/index");
      }
    });
  });
};

var queueUrl = "../queues/process/";
var processQueue = new ProcessQueue(queueUrl);
//processQueue.init();
processQueue.initBasicButtons();

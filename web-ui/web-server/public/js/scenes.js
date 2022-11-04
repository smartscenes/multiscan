function createActionButtons(scene) {
  var data_id = 'scene_' + scene.name;
  console.log(data_id);

  var div = $("<div></div>");

  if (scene.queueState && scene.queueState.queued) {
    div.append(
      createButton("Cancel", null, "Remove from process queue")
        .attr(
          "class",
          scene.queueState.running
            ? "btn btn-danger cancelBtn"
            : "btn btn-warning cancelBtn"
        )
        .attr("data-id", data_id)
    );
  } else {
      var custom = [
        "alignpairs",
      ];
      var btnGroup = $("<div></div>")
        .attr("class", "btn-group row")
        .attr("data-id", data_id);
      var process_btn = createButton("Process", null, "Adds to process queue")
        .attr("class", "btn btn-primary processBtn")
        .attr("data-id", data_id)
      var split = $("<button></button")
        .attr("type", "button")
        .attr("class", "btn btn-primary dropdown-toggle dropdown-toggle-split")
        .attr("data-toggle", "dropdown")
        .attr("aria-haspopup", "true")
        .attr("aria-expanded", "false")
        .append('<span class="caret"></span>');
      btnGroup.append(process_btn);
      btnGroup.append(split);

      var menu = $("<div></div>")
        .attr("class", "dropdown-menu")
        .attr("role", "menu");
      for (var i = 0; i < custom.length; i++) {
        menu
          .append('<div class="btn-group-toggle" data-toggle="buttons">')
          .append(
            $("<label></label>")
              .text(custom[i])
              .attr("class", "btn btn-secondary active")
              .attr("tabindex", "-1")
          )
          .append(
            $('<input type="checkbox" checked>')
              .attr("name", custom[i])
              .attr("data-id", data_id)
            );
      }
      btnGroup.append(menu);
      div.append(btnGroup);
  }

  return div;
}

function initResultTable(params) {
  var lazyImgLoadCallback = $.fn.dataTable.getLazyImgLoadCallback();
  var resultTable = $("#resultTable");
  resultTable.dataTable({
    "lengthMenu": [[25, 50, 100, -1], [25, 50, 100, "All"]],
    "order": [],
    "deferRender": false,
    "stateSave": true,
    "dom": 'BlfripFtip',
    "buttons": [
      'csv', 'colvis', 'orderNeutral', 'selectAll', 'selectNone'
    ],
    "select": {
        style:    'multi'
    },
    "columns": [
        { "data": "name" },
        { "data": "type" },
        { "data": "scans" },
        { // Scans
          "orderable":      false,
          "searchable":     false
        },
        { // Segs
          "orderable":      false,
          "searchable":     false
        },
        { // Action buttons
          "orderable":      false,
          "searchable":     false
        },
        {
          // Process buttons
          orderable: false,
          searchable: false,
          data: null,
          defaultContent: "",
          render: function (data, type, full, meta) {
            return getHtml(createActionButtons(full));
          }
        }
    ],
    "rowCallback": function( row, aData, iDisplayIndex ) {
      //console.log(row, aData, iDisplayIndex);
      lazyImgLoadCallback(row, aData, iDisplayIndex);
      processQueue.initProcessButtons(row);
      return row;
    },
    "initComplete": function() {
      $.fn.dataTable.addColumnFilters({ table: resultTable });
      resultTable.css('visibility', 'visible');
      $('#loadingMessage').hide();
    }
  });

}

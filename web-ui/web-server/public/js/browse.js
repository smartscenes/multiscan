  var ModelViewer = STK.ModelViewer;
  var tabsDiv = $('#tabs');
  tabsDiv.tabs().css({ 'min-height': '400px', 'overflow': 'auto' });
  var canvas = document.getElementById('canvas');
  var modelViewer = new ModelViewer({
    container: canvas,
    sources: ['vf'],
    useNewImages: true,
    tooltipIncludeExtraFields: ['sceneLabel', 'sceneType'],
    partsPanel: {
      partTypes: ['none', 'surfaces', 'voxels-solid', 'voxels-surface', 'voxels-labeled'],
      defaultPartType: 'none',
      defaultLabelType: 'Raw'
    }
  });
  var modelId = getUrlParam('modelId');
  var multiscanStagingIndexPath = '/data/multiscan/scans/staging/multiscan';
  var multiscanCheckedIndexPath = '/data/multiscan/scans/checked/multiscan';
  var nyuv2IndexPath = '/data/external/nyuv2/nyuv2';
  modelViewer.launch();
  modelViewer.registerCustomModelAssetGroup(multiscanStagingIndexPath + '.csv', multiscanStagingIndexPath + '.json',
    (modelId && modelId.startsWith('scan-staging')) ? 'fullId:' + modelId : undefined);
  modelViewer.registerCustomModelAssetGroup(multiscanCheckedIndexPath + '.csv', multiscanCheckedIndexPath + '.json',
    (modelId && modelId.startsWith('scan-checked')) ? 'fullId:' + modelId : (!(modelId)? 'hasCleaned:True' : undefined) );
  modelViewer.registerCustomModelAssetGroup(nyuv2IndexPath + '.csv', nyuv2IndexPath + '.json',
    (modelId && modelId.startsWith('nyuv2')) ? 'fullId:' + modelId : undefined);
  tabsDiv.bind('tabsactivate', function (event, ui) {
    switch (ui.newPanel.attr('id')) {
      case 'tabs-1':
        modelViewer.modelSearchController.onResize();
        break;
      case 'tabs-7':
        modelViewer.modelImagesPanel.onResize();
        break;
    }
  });
  $('#instructions').hide();
  $('#instructionsPanel').click(function () {
    $('#instructions').toggle();
  });
  // Make various components draggable
  $('#namesPanel').draggable();
  $('#customLoadingPanel').draggable();
  $('#instructionsPanel').draggable();
  window.app = modelViewer;  // For console debugging

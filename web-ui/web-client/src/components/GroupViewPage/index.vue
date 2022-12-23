<template>
  <v-container fluid class="d-flex justify-center">
    <v-card elevation="5" class="my-10 px-6 pt-5 pb-2" width="95%" max-width="1900">
      <!-- Table header -->
      <v-row class="px-2" align="center">
        <v-col>
          <h2>{{ tableInfo.title }}</h2>
        </v-col>
        <v-col xl="4" lg="5" md="6" sm="12" cols="12">
          <v-text-field
            v-model="tableInfo.search"
            clearable
            color="primary"
            outlined
            dense
            placeholder="Search"
            hide-details
            prepend-inner-icon="mdi-magnify"
            label="Search"
          ></v-text-field>
        </v-col>
      </v-row>
      <v-row v-if="$route.query.type === 'sceneTypes'" class="px-2">
        <v-col>
          <v-btn color="primary" @click="showChartDialog.showDialog = true">View Chart</v-btn>
        </v-col>
      </v-row>
      <!-- Table -->
      <v-data-table
        class="mt-3"
        :loading="tableInfo.isTableLoading"
        :headers="tableInfo.tableHeaders"
        :items="tableInfo.tableData"
        :search="tableInfo.search"
        :footer-props="{'show-first-last-page': true, 'items-per-page-options': [20, 50, -1],
                'items-per-page-all-text': 'All', 'items-per-page-text': 'Items / Page'}">
        <template v-if="$route.query.type === 'sceneNames'" v-slot:item.thumbnails="{item}">
          <div class="d-flex flex-row">
            <img v-for="scanID in item.scanIDs" :key="scanID.value" style="object-fit: contain; width: 120px;"
                 :src="config.externalURLs.serverBaseURL + '/' + scanID + '/v1.1/' + scanID + '_postalign.png'"/>
          </div>
        </template>
        <template v-slot:item.actions="{item}">
          <v-btn color="primary" :to="{name: 'ScansPage', query: {[tableInfo.queryKey]: item.key}}">
            View
          </v-btn>
          <v-btn color="primary" v-if="$route.query.type === 'sceneNames'" class="ml-5"
                 @click="openAlignScanDialog(item.scanIDs, item.key, item.sceneType)">
            Align
          </v-btn>
        </template>
      </v-data-table>
    </v-card>
    <!-- Dialogs -->
    <show-chart-dialog v-model="showChartDialog.showDialog" :chart-options="showChartDialog.chartOptions"
                       :values="showChartDialog.values"></show-chart-dialog>
    <align-scan-dialog v-model="alignScanDialog.showDialog"
                       :scans="alignScanDialog.selectedScanInfo"></align-scan-dialog>

    <!-- Message Bar -->
    <v-snackbar :color=snackBarInfo.snackBarColor timeout=2000 top v-model="snackBarInfo.showSnackBar">
      {{ snackBarInfo.snackBarText }}
    </v-snackbar>

  </v-container>

</template>

<script>
import ShowChartDialog from "@/components/GroupViewPage/Dialog/ShowChartDialog";
import AlignScanDialog from "@/components/ScansPage/Dialog/AlignScanDialog";

export default {
  name: "GroupViewPage",
  components: {ShowChartDialog, AlignScanDialog},
  data() {
    return {
      config: this.$config,
      snackBarInfo: {
        snackBarColor: null,
        showSnackBar: false,
        snackBarText: null,
      },
      alignScanDialog: {
        selectedScanInfo: [],
        showDialog: false,
      },
      tableInfo: {
        tableHeaders: [],
        tableData: [],
        isTableLoading: true,
        search: '',
        title: '',
        queryKey: ''
      },
      chartValues: [],
      showChartDialog: {
        showDialog: false,
        chartOptions: {
          chart: {
            type: 'donut',
          },
          legend: {
            fontSize: "19"
          },
          labels: [],
        },
        values: []
      },

    }
  },
  methods: {
    getTagsTableData() {
      this.tableInfo.isTableLoading = true;
      this.tableInfo.tableData = []
      this.tableInfo.tableHeaders = [
        {
          text: 'Tag Name',
          value: 'key',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Scans',
          value: 'scansCount',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Actions',
          value: 'actions',
          sortable: false,
          filterable: false,
          class: 'subtitle-2 font-weight-bold',
        },
      ]
      let that = this;
      this.$http.get('/api/stats/tags').then(function (response) {
        for (let item of response.data) {
          that.tableInfo.tableData.push({key: item.name, scansCount: item.scans})
        }
        that.tableInfo.isTableLoading = false;
      })
    },
    getDevicesTableData() {
      this.tableInfo.isTableLoading = true;
      this.tableInfo.tableData = []
      this.tableInfo.tableHeaders = [
        {
          text: 'Device ID',
          value: 'key',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Device Name',
          value: 'deviceName',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Scans',
          value: 'scansCount',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Actions',
          value: 'actions',
          sortable: false,
          filterable: false,
          class: 'subtitle-2 font-weight-bold',
        },
      ]
      let that = this;
      this.$http.get('/api/stats/device_ids').then(function (response) {
        for (let item of response.data) {
          that.tableInfo.tableData.push({key: item.id, deviceName: item.names[0], scansCount: item.scans})
        }
        that.tableInfo.isTableLoading = false;
      })
    },
    cancelAllTableSelection() {
      // dummy
    },
    getUsersTableData() {
      this.tableInfo.isTableLoading = true;
      this.tableInfo.tableData = []
      this.tableInfo.tableHeaders = [
        {
          text: 'User Name',
          value: 'key',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Scans',
          value: 'scansCount',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Actions',
          value: 'actions',
          sortable: false,
          filterable: false,
          class: 'subtitle-2 font-weight-bold',
        },
      ]
      let that = this;
      this.$http.get('/api/stats/users').then(function (response) {
        for (let item of response.data) {
          that.tableInfo.tableData.push({key: item.name, scansCount: item.scans})
        }
        that.tableInfo.isTableLoading = false;
      })
    },
    getSceneNamesTableData() {
      this.tableInfo.isTableLoading = true;
      this.tableInfo.tableData = [];
      this.tableInfo.tableHeaders = [
        {
          text: 'Scene Name',
          value: 'key',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Scene Type',
          value: 'sceneType',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: '#Scans',
          value: 'scansCount',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Thumbnails',
          value: 'thumbnails',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Actions',
          value: 'actions',
          sortable: false,
          filterable: false,
          class: 'subtitle-2 font-weight-bold',
        },
      ]
      let that = this;
      this.$http.get('/api/stats/scenes_names').then(function (response) {
        for (let item of response.data) {
          that.tableInfo.tableData.push({
            key: item.name,
            sceneType: item.type[0],
            scansCount: item.scanCount,
            scanIDs: item.scanIds
          })
        }
        that.tableInfo.isTableLoading = false;
      })
    },
    getSceneTypesTableData() {
      this.tableInfo.isTableLoading = true;
      this.tableInfo.tableData = []
      this.tableInfo.tableHeaders = [
        {
          text: 'Scene Type',
          value: 'key',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Scans',
          value: 'scansCount',
          class: 'subtitle-2 font-weight-bold',
        },
        {
          text: 'Actions',
          value: 'actions',
          sortable: false,
          filterable: false,
          class: 'subtitle-2 font-weight-bold',
        },
      ]
      let that = this;
      this.$http.get('/api/stats/scenes_types').then(function (response) {
        for (let item of response.data) {

          that.tableInfo.tableData.push({key: item.type, scansCount: item.scans})
          that.showChartDialog.values.push(item.scans)
          that.showChartDialog.chartOptions.labels.push(item.type)

        }
        that.tableInfo.isTableLoading = false;
      })
    },
    showMessageBar(message, type) {
      this.snackBarInfo.snackBarColor = type;
      this.snackBarInfo.snackBarText = message;
      this.snackBarInfo.showSnackBar = true;
    },
    updatePage() {
      switch (this.$route.query.type) {
        case "sceneNames":
          this.tableInfo.title = "Scene Names";
          this.tableInfo.queryKey = "sceneName"
          this.getSceneNamesTableData();
          break;
        case "sceneTypes":
          this.tableInfo.title = "Scene Types";
          this.tableInfo.queryKey = "sceneType"
          this.showChartDialog.values = []
          this.showChartDialog.chartOptions.labels = []
          this.getSceneTypesTableData();
          break;
        case "tags":
          this.tableInfo.title = "Tags";
          this.tableInfo.queryKey = "tags"
          this.getTagsTableData();
          break;
        case "users":
          this.tableInfo.title = "Users";
          this.tableInfo.queryKey = "userName"
          this.getUsersTableData();
          break;
        case "devices":
          this.tableInfo.title = "Devices";
          this.tableInfo.queryKey = "deviceId"
          this.getDevicesTableData();
          break;
      }
    },
    openAlignScanDialog(scanIDs, sceneName, sceneType) {
      this.alignScanDialog.selectedScanInfo = []
      for (let scanID of scanIDs) {
        this.alignScanDialog.selectedScanInfo.push(
          {
            id: scanID,
            previewUrl: "/multiscan/webui/data/multiscan/scans/staging/" + scanID + "/v1.1/" + scanID + "_obj_thumb.png",
            alignThumbUrl: "/multiscan/webui/data/multiscan/scans/staging/" + scanID + "/v1.1/" + scanID + "_postalign.png",
            sceneName: sceneName,
            sceneType: sceneType
          }
        );
      }
      this.alignScanDialog.showDialog = true;
    },
  },
  mounted() {
    this.updatePage();
  },
  watch: {
    '$route'() {
      this.updatePage();
    }
  }
}
</script>

<style scoped>

</style>

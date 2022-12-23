<template>
  <v-dialog v-model="showDialog" persistent width="1000">
    <v-card>
      <v-card-title style="opacity: 0.8">
        <span>Align Scans</span>
        <v-spacer></v-spacer>
        <v-btn icon @click="close" :disabled="isLoading">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-subtitle>
        <div v-if="ifSceneNameMatch" class="d-flex align-center mt-3">
          <v-icon size="19" color="green" class="mr-1">mdi-check-circle-outline</v-icon>
          <span class="green--text">All scene names match</span>
        </div>
        <div v-else class="d-flex align-center mt-3">
          <v-icon size="19" color="error" class="mr-1">mdi-alert-circle-outline</v-icon>
          <span class="error--text">Warning: Scene names do not match</span>
        </div>
        <div v-if="ifSceneTypeMatch" class="d-flex align-center">
          <v-icon size="19" color="green" class="mr-1">mdi-check-circle-outline</v-icon>
          <span class="green--text">All scene types match</span>
        </div>
        <div v-else class="d-flex align-center">
          <v-icon size="19" color="error" class="mr-1">mdi-alert-circle-outline</v-icon>
          <span class="error--text">Warning: Scene types do not match</span>
        </div>
      </v-card-subtitle>
      <v-card-text>
        <v-sheet rounded style="outline: 1px solid black; opacity: 0.7" class="mx-1 mt-3 mb-6 pb-1 px-2" >
          <div style="display: inline-block; transform: translate(0, -50%); background-color: white;" class="ml-3 px-3">
            <span >Reference Scan</span>
          </div>

          <v-row v-if="referenceScanInfo.id">
            <v-col cols="auto">
              <img :src="config.externalURLs.serverBaseURL + referenceScanInfo.previewUrl"
                   style="object-fit: contain; width: 120px;" alt="preview" class="mt-1">
            </v-col>
            <v-col>
              <div class="align-center mb-2">
                <v-chip color="grey darken-1"
                        label
                        small
                        text-color="white">
                  Scan ID
                </v-chip>
                <span class="mx-2">{{ referenceScanInfo.id }}</span>
              </div>
              <div class="align-center mb-2">
                <v-chip color="grey darken-1"
                        label
                        small
                        text-color="white">
                  Scene ID
                </v-chip>
                <span class="mx-2">{{ referenceScanInfo.sceneName }}</span>
              </div>
              <div class="align-center mb-2">
                <v-chip color="grey darken-1"
                        label
                        small
                        text-color="white">
                  Scene Type
                </v-chip>
                <span class="mx-2">{{ referenceScanInfo.sceneType }}</span>
              </div>
            </v-col>
          </v-row>
          <div v-else class="ma-3" style="width: 100%">
            <p style="text-align: center;">Please select a reference scan</p>
          </div>



        </v-sheet>
        <v-simple-table fixed-header>
          <template v-slot:default>
            <thead>
            <tr>
              <th class="text-left">Preview</th>
              <th class="text-left">Thumbnail</th>
              <th class="text-left">Scan ID</th>
              <th class="text-left">Scene ID</th>
              <th class="text-left">Scene Type</th>
              <th class="text-left">Reference</th>
            </tr>
            </thead>
            <tbody>
              <template v-for="item in scans">
                <tr v-if="!item.isRef" :key="item.id">
                  <td>
                    <img :src="config.externalURLs.serverBaseURL + item.previewUrl"
                         style="object-fit: contain; width: 120px;" alt="preview" class="mt-1">
                  </td>
                  <td>
                    <img :src="config.externalURLs.serverBaseURL + item.alignThumbUrl"
                         style="object-fit: contain; width: 120px;" alt="thumbnail" class="mt-1">
                  </td>
                  <td>{{ item.id }}</td>
                  <td>{{ item.sceneName }}</td>
                  <td>{{ item.sceneType }}</td>
                  <td>
                    <v-btn small color="primary" @click="chooseAsRef(item.id)">Select</v-btn>
                  </td>
                </tr>
              </template>

            </tbody>
          </template>
        </v-simple-table>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions class="pb-4 mx-1 mt-1">
        <!--                <span style="opacity: 0.7; font-size: 13px" class="mr-4">{{ selectedCount }} Selected<br/>Total Size: {{ selectedTotalSize }}</span>-->
        <v-spacer></v-spacer>
        <v-btn color="primary" :loading="isLoading" @click="submitAllProcesses" :disabled="!referenceScanInfo.id">
          Align
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: "AlignScanDialog",
  model: {
    prop: 'showDialog',
    event: 'closeDialog'
  },
  props: {
    showDialog: Boolean,
    scans: Array,
  },
  data() {
    return {
      config: this.$config,
      isLoading: false,
      ifSceneTypeMatch: true,
      ifSceneNameMatch: true,
      referenceScanInfo: {
        id: null,
        sceneName: null,
        sceneType: null,
        previewUrl: null
      }
    }
  },

  methods: {
    close() {
      this.referenceScanInfo.id = null
      this.referenceScanInfo.sceneName = null
      this.referenceScanInfo.sceneType = null
      this.referenceScanInfo.previewUrl = null
      this.$emit('closeDialog', false);
    },
    chooseAsRef(itemID) {
      for (let item of this.scans) {
        if (item.id === itemID) {
          item.isRef = true
          // Hacky way to trigger a refreshing of the bound view
          let tmp = item.id
          item.id = null
          item.id = tmp

          this.referenceScanInfo.id = item.id
          this.referenceScanInfo.sceneName = item.sceneName
          this.referenceScanInfo.sceneType = item.sceneType
          this.referenceScanInfo.previewUrl = item.previewUrl

        } else {
          item.isRef = false
        }

      }

    },
    checkConsistency() {
      this.ifSceneTypeMatch = true;
      this.ifSceneNameMatch = true;
      for (let i = 0; i < this.scans.length; i++) {
        if (this.scans[i].sceneType !== this.scans[0].sceneType) {
          this.ifSceneTypeMatch = false
        }
        if (this.scans[i].sceneName !== this.scans[0].sceneName) {
          this.ifSceneNameMatch = false
        }
      }
    },
    submitEdit() {
      this.isLoading = true;
      let requestBody = {action: "edit", data: {}};
      for (let scan of this.scans) {
        requestBody.data[scan.id] = {
          isRef: scan.id === this.referenceScanInfo.id,
        };
      }
      return this.$http.post('/scans/edit', requestBody);
    },
    submitProcess(id) {
      let params = new URLSearchParams();
      params.append("scanId", id)
      params.append("overwrite", "1")
      params.append("actions", '["alignpairs"]')
      return this.$http.post('/queues/process/add', params);
    },
    submitAllProcesses() {
      let that = this;
      this.isLoading = true;
      let processes = []
      processes.push(this.submitEdit())
      for (let scan of this.scans) {
        processes.push(this.submitProcess(scan.id))
      }
      this.$http.all(processes).then(that.$http.spread((...response) => {
        let success = true;
        [...response].forEach((item) => {
          if (item.status !== 200) {
            success = false
          }
        })
        if (success) {
          that.$parent.showMessageBar("Process task is being queued", "success")
          that.$parent.getTableData(false);
        } else {
          that.$parent.showMessageBar("Error: Fail to process", "error")
        }
        that.isLoading = false;
        that.$parent.cancelAllTableSelection()
        that.close()
      }))
    },
    validRefs() {

      for (let item of this.scans) {
        if (item.isRef) {
          this.referenceScanInfo.id = item.id;
          this.referenceScanInfo.sceneName = item.sceneName;
          this.referenceScanInfo.sceneType = item.sceneType;
          this.referenceScanInfo.previewUrl = item.previewUrl;
          break;
        }
      }
    }
  },
  beforeUpdate() {
    this.checkConsistency()
    this.validRefs()
  }
}
</script>

<style scoped>

</style>

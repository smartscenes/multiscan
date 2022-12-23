<template>
  <div>
    <v-dialog v-model="showDialog" width="770" scrollable>
      <v-card>
        <div class="d-flex align-center mt-5 mb-3 px-6">
          <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
          <span style="opacity: 0.8;" class="text-h6">Process Queue</span>
          <v-spacer></v-spacer>
          <v-tooltip bottom v-if="isPaused">
            <template v-slot:activator="{ on, attrs }">
              <v-btn color="primary" v-bind="attrs" v-on="on" @click="submitResumeQueue"
                     :loading="isLoading">
                <v-icon small color="white" class="mr-1">mdi-play</v-icon>
                Resume
              </v-btn>
            </template>
            <span>Resume the process queue</span>
          </v-tooltip>

          <v-tooltip bottom v-else>
            <template v-slot:activator="{ on, attrs }">
              <v-btn color="primary" v-bind="attrs" v-on="on" @click="submitPauseQueue"
                     :loading="isLoading">
                <v-icon small color="white" class="mr-1">mdi-pause</v-icon>
                Pause
              </v-btn>
            </template>
            <span>Pause the process queue</span>
          </v-tooltip>

          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <v-btn color="warning" class="ml-2" v-bind="attrs" v-on="on"
                     @click="clearQueueDialog.showDialog = true"
                     :loading="clearQueueDialog.isLoading">
                Clear All
              </v-btn>
            </template>
            <span>Clear the process queue</span>
          </v-tooltip>
        </div>
        <v-divider></v-divider>
        <v-card-text class="px-6 mx-0">
          <v-list>
            <template v-for="(item, index) in queuedData">
              <div :key="item.id" class="py-3 d-flex align-center justify-center">
                <img v-if="item.videoThumbnailUrl"
                     :src="config.externalURLs.serverBaseURL + item.videoThumbnailUrl"
                     style="object-fit: contain; height: 80px" class="mr-4" alt="">
                <p v-else class="text-center my-5 mr-9 ml-5">No Video<br/>Thumbnail</p>
                <div class="mr-7">
                  <span style="opacity: 0.8; font-size: 14px">ID: {{ item.id }}</span><br/>
                  <span style="opacity: 0.7; font-size: 13px">Device: {{
                      item.deviceName
                    }}</span><br/>
                  <v-chip color="success" label x-small v-if="item.queueState.running">Running
                  </v-chip>
                </div>
                <v-spacer></v-spacer>
                <v-btn outlined color="error" v-if="item.queueState.running" width="86"
                       @click="submitRemoveProcess(item.id)">
                  Cancel
                </v-btn>
                <v-btn outlined color="warning" v-else width="86" @click="submitRemoveProcess(item.id)">
                  Remove
                </v-btn>
              </div>
              <v-divider :key="index"></v-divider>
            </template>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>
    <v-dialog
      v-model="clearQueueDialog.showDialog"
      persistent
      max-width="350">
      <v-card>
        <v-card-title>
          <v-icon class="mr-1" color="black">mdi-alert-circle-outline</v-icon>
          Warning
        </v-card-title>
        <v-card-text>
          Are you sure you want to clear the process queue? All processes will be lost.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="clearQueueDialog.showDialog = false">Cancel</v-btn>
          <v-btn color="primary" text @click="submitClearQueue"
                 :loading="clearQueueDialog.isLoading">
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  name: "QueueDialog",
  props: {
    showDialog: Boolean,
    queuedData: Array
  },
  model: {
    prop: 'showDialog',
    event: 'closeDialog'
  },
  data() {
    return {
      config: this.$config,
      isLoading: false,
      // queuedData: [],
      isPaused: false,
      clearQueueDialog: {
        showDialog: false,
        isLoading: false,
      },
    }
  },
  methods: {
    close() {
      this.$emit('closeDialog', false);
    },
    submitClearQueue() {
      let that = this;
      this.clearQueueDialog.isLoading = true;
      this.$http.get('/queues/process/clear').then(function (response) {
        if (response.status === 200) {
          that.clearQueueDialog.showDialog = false;
          that.clearQueueDialog.isLoading = false;
          that.$parent.reindex();
          that.getQueueStatus();
        }
      })
    },
    submitPauseQueue() {
      let that = this;
      this.queuedInfo.isQueuedMenuLoading = true;
      this.$http.get('/queues/process/pause').then(function (response) {
        that.queuedInfo.isQueuedMenuLoading = false;
        if (response.status === 200) {
          that.getQueueStatus();
          that.$parent.showMessageBar("Pause the process queue successfully", "success")
        } else {
          that.$parent.showMessageBar("Error: Fail to pause the process queue", "error")
        }
      })
    },
    submitResumeQueue() {
      let that = this;
      this.queuedInfo.isQueuedMenuLoading = true;
      this.$http.get('/queues/process/resume').then(function (response) {
        if (response.status === 200) {
          that.queuedInfo.isQueuedMenuLoading = false;
          that.getQueueStatus();
          that.$parent.showMessageBar("Resume the process queue successfully", "success")
        } else {
          that.$parent.showMessageBar("Error: Fail to resume the process queue", "error")
        }
      })
    },
    getQueueStatus() {
      let that = this;
      this.$http.get('/queues/process/stats').then(function (response) {
        if (response.status === 200) {
          that.queuedInfo.isPaused = response.data.isPaused
          if (that.queuedInfo.size === 0) {
            that.showQueuedMenu = false;
          }
        }
      })
    },
    submitRemoveProcess(id) {
      let that = this;
      this.$http.get('/queues/process/remove', {params: {scanId: id,}}).then(function (response) {
        if (response.status === 200) {
          that.$http.get('/scans/index/' + id).then(function (response) {
            if (response.status === 200) {
              that.$parent.showMessageBar("Process has been removed from the queue", "success")
              that.$parent.getTableData()
            } else {
              that.$parent.showMessageBar("Error: Fail to remove the process", "error")
            }
            if (that.queueedCount === 0) {
              that.showQueuedMenu = false;
            }
          })
        }
      })
    },
  },
  computed: {
    queueedCount() {
      return this.queuedInfo.queuedData.length;
    },
  },
}
</script>

<style scoped>

</style>

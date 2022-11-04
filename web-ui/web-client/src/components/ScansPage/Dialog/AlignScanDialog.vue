<template>
    <v-dialog v-model="showDialog" persistent width="800">
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
                <v-simple-table fixed-header>
                    <template v-slot:default>
                        <thead>
                            <tr>
                                <th class="text-left">Preview</th>
                                <th class="text-left">Thumbnail</th>
                                <th class="text-left">ID</th>
                                <th class="text-left">Scene Name</th>
                                <th class="text-left">Scene Type</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="item in scans" :key="item.id">
                                <td>
                                    <img :src="'http://spathi.cmpt.sfu.ca' + item.previewUrl"
                                         style="object-fit: contain; width: 120px;" alt="preview" class="mt-1">
                                </td>
                              <td>
                                <img :src="'http://spathi.cmpt.sfu.ca' + item.alignThumbUrl"
                                     style="object-fit: contain; width: 120px;" alt="thumbnail" class="mt-1">
                              </td>
                                <td>{{ item.id }}</td>
                                <td>{{ item.sceneName }}</td>
                                <td>{{ item.sceneType }}</td>
                            </tr>
                        </tbody>
                    </template>
                </v-simple-table>
            </v-card-text>
            <v-divider></v-divider>
            <v-card-actions class="pb-4 mx-1 mt-1">
<!--                <span style="opacity: 0.7; font-size: 13px" class="mr-4">{{ selectedCount }} Selected<br/>Total Size: {{ selectedTotalSize }}</span>-->
                <v-spacer></v-spacer>
                <v-btn color="primary" :loading="isLoading" @click="submitAllProcesses">
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
            isLoading: false,
            ifSceneTypeMatch: true,
            ifSceneNameMatch: true,
        }
    },
    methods: {
        close() {
            this.$emit('closeDialog', false);
        },
        checkConsistency(){
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
        submitProcess(id) {
            return this.$http.post('/queues/process/add', {
                scanId: id,
                overwrite: 1,
                actions: ["alignpairs"]
            });
        },
        submitAllProcesses() {
            let that = this;
            this.isLoading = true;
            let processes = []
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
                } else {
                    that.$parent.showMessageBar("Error: Fail to process", "error")
                }
                that.isLoading = false;
                that.$parent.cancelAllTableSelection()
                that.close()
            }))
        }
    },
    beforeUpdate() {
        this.checkConsistency()
        console.log(this.scans)
    }
}
</script>

<style scoped>

</style>

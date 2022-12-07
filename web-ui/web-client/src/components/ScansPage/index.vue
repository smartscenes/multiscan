<template>
    <v-container fluid class="d-flex justify-center">
        <v-card elevation="5" class="my-10 px-5 pt-5 pb-2" width="95%" max-width="1900">
            <!-- Table header -->
            <v-row align="center" class="px-2">
                <v-col v-if="tableInfo.selectedRows.length === 0">
                    <v-menu open-on-hover offset-y >
                        <template v-slot:activator="{ on, attrs }">
                            <v-btn v-bind="attrs" v-on="on" color="primary" class="mr-3 my-2">
                                <v-icon small color="white" class="mr-2">mdi-eye</v-icon>
                                Column Visibility
                            </v-btn>
                        </template>

                        <v-list dense class="pb-0">
                            <v-list-item v-for="item in tableInfo.cols" :key="item.value" dense style="min-height: 31px">
                                <v-checkbox
                                    class="my-0 py-0"
                                    dense
                                    v-model="tableInfo.selectedCols"
                                    :label="item.text"
                                    :value="item"
                                    hide-details
                                ></v-checkbox>
                            </v-list-item>
                            <v-divider class="mt-2"></v-divider>
                            <v-btn text color="primary" block @click="loadColVisibility(true)" height="40">
                                <v-icon color="primary" small class="mr-1">mdi-cached</v-icon>
                                Reset
                            </v-btn>
                        </v-list>
                    </v-menu>
                    <v-btn color="primary" @click="reindex" :loading="isReindexBtnLoading" class="my-2 mr-3">
                        <v-icon small color="white" class="mr-1">mdi-refresh</v-icon>
                        Reindex
                    </v-btn>
                    <v-btn color="primary" class="mr-3 my-2" @click="downloadCSV">
                        <v-icon small color="white" class="mr-1">mdi-download</v-icon>
                        Download CSV
                    </v-btn>
                    <v-badge color="green" overlap :content="queueedCount" bordered>
                        <v-btn color="primary" outlined my-2
                               @click="queueedCount !== '0' ? queueDialog.showDialog = true : showMessageBar('Process queue is empty', 'info')">
                            <v-icon small color="primary" class="mr-1">mdi-format-list-bulleted</v-icon>
                            Queued
                        </v-btn>
                    </v-badge>
                </v-col>
                <v-col v-else>
                    <div class="d-flex align-center py-2">
                        <span class="text--secondary">{{tableInfo.selectedRows.length}} Selected</span>
                        <v-divider class="mx-5" vertical></v-divider>
                        <v-btn :disabled="tableInfo.selectedRows.length < 2" color="primary" @click="openAlignScanDialog">
                            <v-icon small color="white" class="mr-2">mdi-cards</v-icon>
                            Align Scans
                        </v-btn>
                        <v-btn color="primary" class="mx-4" @click="openEditScanInfoDialog(tableInfo.selectedRows)">
                            <v-icon small color="white" class="mr-2">mdi-pencil</v-icon>
                            Edit All
                        </v-btn>
                        <v-menu
                            open-on-hover
                            transition="slide-y-transition"
                            :close-on-content-click="false"
                            :nudge-width="96">
                            <template v-slot:activator="{ on, attrs }">
                                <v-btn color="primary" v-bind="attrs" v-on="on">
                                    Process All
                                </v-btn>
                            </template>
                            <v-card rounded class="px-3 py-2">
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Convert"
                                            value="convert"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Recons"
                                            value="recons"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Texturing"
                                            value="texturing"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Photogrammetry" value="photogrammetry"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Knownposes"
                                            value="knownposes"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Segmentation"
                                            value="segmentation"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Render"
                                            value="render"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Thumbnail"
                                            value="thumbnail"></v-checkbox>
                                <div class="d-flex flex-row-reverse mt-3 mb-1">
                                    <v-btn small depressed color="primary" @click="submitAllProcesses"
                                           :loading="isProcessBtnLoading">
                                        Confirm
                                    </v-btn>
                                </div>
                            </v-card>
                        </v-menu>


                    </div>
                </v-col>
                <v-col xl="4" lg="4" md="5" sm="12" cols="12">
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
            <!-- Table -->
            <v-data-table
                single-expand
                show-select
                v-model="tableInfo.selectedRows"
                mobile-breakpoint="0"
                :loading="tableInfo.isTableLoading"
                :headers="tableInfo.tableHeaders"
                sort-by="createdAt"
                :sort-desc="true"
                :items="tableInfo.tableData"
                :expanded.sync="tableInfo.expanded"
                :search="tableInfo.search"
                :footer-props="{'show-first-last-page': true, 'items-per-page-options': [10, 30, 50, -1],
                'items-per-page-all-text': 'All', 'items-per-page-text': 'Items / Page'}"
                show-expand>
                <template v-slot:item.videoThumbnailUrl="{ item }">
                    <div class="d-flex justify-center">
                        <p v-if="item.videoThumbnailUrl === undefined || item.videoMp4Url === undefined"
                           class="text-center py-6 my-0">No<br/>Video</p>
                        <img v-else :src="'http://spathi.cmpt.sfu.ca' + item.videoThumbnailUrl"
                             style="object-fit: contain; width: 120px; cursor: pointer;" alt="video"
                             @click="openPlayVideoDialog('http://spathi.cmpt.sfu.ca' + item.videoMp4Url)"
                             class="my-1">
                    </div>
                </template>
                <template v-slot:item.previewUrl="{ item }">
                    <div class="d-flex justify-center">
                        <p v-if="item.previewUrl === undefined" class="text-center py-6 my-0">No<br/>Preview</p>
                        <v-menu absolute offset-y style="max-width: 600px" v-else>
                            <template v-slot:activator="{ on, attrs }">
                                <img :src="'http://spathi.cmpt.sfu.ca' + item.previewUrl" v-bind="attrs" v-on="on"
                                     style="object-fit: contain; width: 120px; cursor: pointer;"
                                     alt="preview"
                                     class="my-1">
                            </template>
                            <v-list dense>
                                <v-list-item dense
                                             v-for="(item2, index) in [{title: 'Original', value: 'original'}, {title: 'Textured', value: 'textured'}, {title: 'Segmented', value: 'segmented'}]"
                                             :key="index" @click="openAnnotationDialog(item.id, item2.value)">
                                    <v-list-item-title>{{ item2.title }}</v-list-item-title>
                                </v-list-item>
                            </v-list>
                        </v-menu>

                    </div>
                </template>
                <template v-slot:item.sceneType="props">
                    <v-edit-dialog
                        :return-value.sync="props.item.sceneType"
                        @save="submitOneEdit(props.item.id, 'sceneType', props.item.sceneType)">
                        {{ props.item.sceneType }}
                        <template v-slot:input>
                            <v-select
                                style="width: 250px"
                                hide-details
                                class="my-4"
                                v-model="props.item.sceneType"
                                label="Scene Type"
                                :items="['Apartment', 'Bathroom', 'Bedroom / Hotel', 'Bookstore / Library', 'Classroom',
                                'Closet', 'Conference Room', 'Dining Room', 'Hallway', 'Kitchen', 'Living room / Lounge',
                                'Lobby', 'Office', 'Misc.', 'Laundry Room', 'Storage/Basement/Garage', 'Mailboxes']"
                                dense
                                outlined
                            ></v-select>
                        </template>
                    </v-edit-dialog>
                </template>
                <template v-slot:item.tags="props">
                    <v-edit-dialog
                        :return-value.sync="props.item.tags"
                        @save="submitOneEdit(props.item.id, 'tags', props.item.tags)">
                        {{ props.item.tags ? props.item.tags.toString() : '' }}
                        <template v-slot:input>
                            <v-combobox
                                style="width: 250px"
                                hide-details
                                :items="editScanInfoDialog.comboBoxItems"
                                dense
                                class="my-4"
                                deletable-chips
                                small-chips
                                multiple
                                label="Tags"
                                outlined
                                v-model="props.item.tags">
                            </v-combobox>
                        </template>
                    </v-edit-dialog>
                </template>
                <template v-slot:item.sceneName="props">
                    <v-edit-dialog
                        :return-value.sync="props.item.sceneName"
                        @save="submitOneEdit(props.item.id, 'sceneName', props.item.sceneName)">
                        {{ props.item.sceneName }}
                        <template v-slot:input>
                            <v-text-field
                                style="width: 150px"
                                hide-details
                                class="my-4"
                                v-model="props.item.sceneName"
                                label="Scene Name"
                                dense
                                outlined
                            ></v-text-field>
                        </template>
                    </v-edit-dialog>
                </template>
                <template v-slot:item.group="props">
                    <v-edit-dialog
                        :return-value.sync="props.item.group"
                        @save="submitOneEdit(props.item.id, 'group', props.item.group)">
                        {{ props.item.group }}
                        <template v-slot:input>
                            <v-select
                                style="width: 150px"
                                hide-details
                                class="my-4"
                                v-model="props.item.group"
                                label="Group"
                                :items="['staging', 'checked', 'bad']"
                                dense
                                outlined
                            ></v-select>
                        </template>
                    </v-edit-dialog>
                </template>
                <template v-slot:item.progress="{ item }">
                    <progress-circle v-bind:stages="item.stages"></progress-circle>
                </template>
                <template v-slot:expanded-item="{ headers, item }">
                    <td :colspan="headers.length">
                        <v-card outlined flat class="my-10 pa-3">
                            <v-card-title>Details:</v-card-title>
                            <v-card-text>
                                <v-row>
                                    <v-col cols="auto">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                ID
                                            </v-chip>
                                            <span class="mx-2">{{ item.id }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.createdAt">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Created At
                                            </v-chip>
                                            <span class="mx-2">{{ item.createdAt.replace("T", " ") }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.updatedAt">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Updated At
                                            </v-chip>
                                            <span class="mx-2">{{ item.updatedAt.replace("T", " ") }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.userName">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                User
                                            </v-chip>
                                            <span class="mx-2">{{ item.userName }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.deviceName">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Device
                                            </v-chip>
                                            <span class="mx-2">{{ item.deviceName }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.sceneType">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Scene Type
                                            </v-chip>
                                            <span class="mx-2">{{ item.sceneType }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.tags && item.tags.length !== 0">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Tags
                                            </v-chip>
                                            <span class="mx-2">{{ item.tags.toString() }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.scanSecs">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Scan Secs
                                            </v-chip>
                                            <span class="mx-2">{{ item.scanSecs.toFixed(2) + "s" }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.processSecs">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Process Secs
                                            </v-chip>
                                            <span class="mx-2">{{ item.processSecs }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.numColorFrames">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Frames
                                            </v-chip>
                                            <span class="mx-2">{{ item.numColorFrames }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.group">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Group
                                            </v-chip>
                                            <span class="mx-2">{{ item.group }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="auto" v-if="item.sceneName">
                                        <div class="align-center">
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Scene Name
                                            </v-chip>
                                            <span class="mx-2">{{ item.sceneName }}</span>
                                        </div>
                                    </v-col>
                                    <v-col cols="12" v-if="item.description">
                                        <div>
                                            <v-chip color="grey darken-1"
                                                    label
                                                    small
                                                    text-color="white">
                                                Scene Description
                                            </v-chip>
                                            <p class="mx-2 mt-1">{{ item.description }}</p>
                                        </div>
                                    </v-col>
                                </v-row>
                            </v-card-text>
                            <v-card-actions class="mt-2">
                                <v-spacer></v-spacer>
                                <v-btn outlined color="primary" dark small
                                       @click="openDownloadFilesDialog(item.id, item.files)"
                                       v-if="item.files && item.files.length !== 0">
                                    <v-icon small color="primary" dark class="mr-1">mdi-file-document-outline</v-icon>
                                    FILES
                                </v-btn>
                            </v-card-actions>
                        </v-card>
                    </td>
                </template>
                <template v-slot:item.actions="{item}" v-if="!isMultipleSelected">
                    <div class="d-flex flex-column">
                        <v-menu
                            v-if="item.group !== 'checked'"
                            open-on-hover
                            :key="item.id"
                            transition="slide-y-transition"
                            :close-on-content-click="false"
                            :nudge-width="96">
                            <template v-slot:activator="{ on, attrs }">
                                <v-btn color="primary" width="76" height="31" v-bind="attrs" v-on="on" small>
                                    Process
                                </v-btn>
                            </template>
                            <v-card rounded class="px-3 py-2">
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Convert"
                                            value="convert"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Recons"
                                            value="recons"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Texturing"
                                            value="texturing"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Photogrammetry" value="photogrammetry"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Knownposes"
                                            value="knownposes"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Segmentation"
                                            value="segmentation"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Render"
                                            value="render"></v-checkbox>
                                <v-checkbox hide-details dense color="primary" v-model="selectedProcessSteps"
                                            label="Thumbnail"
                                            value="thumbnail"></v-checkbox>
                                <div class="d-flex flex-row-reverse mt-3 mb-1">
                                    <v-btn small depressed color="primary" @click="submitOneProcess(item.id)"
                                           :loading="isProcessBtnLoading">
                                        Confirm
                                    </v-btn>
                                </div>
                            </v-card>
                        </v-menu>
                        <v-btn color="primary" width="76" height="31" v-else small
                               @click="openAnnotationDialog(item.id)">
                            Annotate
                        </v-btn>
                        <v-btn color="primary" class="mt-2" outlined width="76" height="31" small
                               @click="openEditScanInfoDialog([item])">
                            <v-icon color="primary" small class="mr-1">mdi-pencil</v-icon>
                            Edit
                        </v-btn>
                    </div>
                </template>
            </v-data-table>
        </v-card>

        <!-- Popup Dialog -->
        <play-video-dialog v-model="playVideoDialog.showDialog"
                           :video-url="playVideoDialog.currentVideoURL"></play-video-dialog>
        <download-file-dialog v-model="downloadFileDialog.showDialog" :file-info="downloadFileDialog.fileInfo"
                              :scan-id="downloadFileDialog.scanId"></download-file-dialog>
<!--        <annotation-dialog v-model="annotationDialog.showDialog"-->
<!--                                :iframe-url="annotationDialog.iframeUrl"></annotation-dialog>-->
        <edit-scan-info-dialog v-model="editScanInfoDialog.showDialog" :combo-box-items="editScanInfoDialog.comboBoxItems"
                               :edit-info="editScanInfoDialog.editInfo"></edit-scan-info-dialog>
<!--        <queue-dialog v-model="queueDialog.showDialog" :queued-data="queueDialog.queuedData"></queue-dialog>-->
        <align-scan-dialog v-model="alignScanDialog.showDialog" :scans="alignScanDialog.selectedScanInfo"></align-scan-dialog>
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
        <v-dialog v-model="queueDialog.showDialog" width="770" scrollable>
            <v-card>
                <div class="d-flex align-center mt-5 mb-3 px-6">
                    <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
                    <span style="opacity: 0.8;" class="text-h6">
                                    Process Queue
                                </span>
                    <v-spacer></v-spacer>
                    <v-tooltip bottom v-if="queuedInfo.isPaused">
                        <template v-slot:activator="{ on, attrs }">
                            <v-btn color="primary" v-bind="attrs" v-on="on" @click="submitResumeQueue"
                                   :loading="queuedInfo.isQueuedMenuLoading">
                                <v-icon small color="white" class="mr-1">mdi-play</v-icon>
                                Resume
                            </v-btn>
                        </template>
                        <span>Resume the process queue</span>
                    </v-tooltip>

                    <v-tooltip bottom v-else>
                        <template v-slot:activator="{ on, attrs }">
                            <v-btn color="primary" v-bind="attrs" v-on="on" @click="submitPauseQueue"
                                   :loading="queuedInfo.isQueuedMenuLoading">
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
                        <template v-for="(item, index) in queuedInfo.queuedData">
                            <div :key="item.id" class="py-3 d-flex align-center justify-center">
                                <img v-if="item.videoThumbnailUrl"
                                     :src="'http://spathi.cmpt.sfu.ca' + item.videoThumbnailUrl"
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
                                       @click="submitRemoveProcess(item.id)">Cancel
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

        <!-- Message Bar -->
        <v-snackbar :color=snackBarInfo.snackBarColor timeout=2000 top v-model="snackBarInfo.showSnackBar">
            {{ snackBarInfo.snackBarText }}
        </v-snackbar>

    </v-container>
</template>

<script>
import ProgressCircle from "@/components/ScansPage/ProgressCircle";
import PlayVideoDialog from "@/components/ScansPage/Dialog/PlayVideoDialog";
import DownloadFileDialog from "@/components/ScansPage/Dialog/DownloadFileDialog";
import EditScanInfoDialog from "@/components/ScansPage/Dialog/EditScanInfoDialog";
import Downloader from "@/utils/download";
import AlignScanDialog from "@/components/ScansPage/Dialog/AlignScanDialog";

export default {
    name: 'ScansPage',
    components: {ProgressCircle, PlayVideoDialog, DownloadFileDialog, EditScanInfoDialog, AlignScanDialog},
    data() {
        return {
            snackBarInfo: {
                snackBarColor: null,
                showSnackBar: false,
                snackBarText: null,
            },
            tableInfo: {
                tableHeaders: [],
                tableData: [],
                isTableLoading: true,
                search: '',
                expanded: [],
                selectedRows: [],
                cols: [
                    {
                        text: 'Video',
                        value: 'videoThumbnailUrl',
                        filterable: false,
                        sortable: false,
                        order: 1,
                    },
                    {
                        text: 'Preview',
                        value: 'previewUrl',
                        filterable: false,
                        sortable: false,
                        order: 2,
                    },
                    {
                        text: 'ID',
                        value: 'id',
                        order: 3,
                    },
                    {
                        text: 'Created At',
                        value: 'createdAt',
                        order: 4,
                    },
                    {
                        text: 'Updated At',
                        value: 'updatedAt',
                        order: 5,
                    },
                    {
                        text: 'Scene Type',
                        value: 'sceneType',
                        order: 6,
                    },
                    {
                        text: 'Tags',
                        value: 'tags',
                        order: 7,
                    },
                    {
                        text: 'User',
                        value: 'userName',
                        order: 8,
                    },
                    {
                        text: 'Scene Name',
                        value: 'sceneName',
                        order: 9,
                    },
                    {
                        text: 'Group',
                        value: 'group',
                        order: 10,
                    },
                    {
                        text: 'Progress',
                        value: 'progress',
                        filterable: false,
                        sortable: false,
                        order: 11,
                    },
                    {
                        text: 'Scan Secs',
                        value: 'scanSecs',
                        order: 12,
                    },
                    {
                        text: 'Process Secs',
                        value: 'processSecs',
                        order: 13,
                    },
                    {
                        text: 'Frames',
                        value: 'numColorFrames',
                        order: 14,
                    },
                ],
                selectedCols: [
                    {
                        text: 'Video',
                        value: 'videoThumbnailUrl',
                        filterable: false,
                        sortable: false,
                        order: 1,
                    },
                    {
                        text: 'Preview',
                        value: 'previewUrl',
                        filterable: false,
                        sortable: false,
                        order: 2,
                    },
                    {
                        text: 'ID',
                        value: 'id',
                        order: 3,
                    },
                    {
                        text: 'Created At',
                        value: 'createdAt',
                        order: 4,
                    },
                    {
                        text: 'Scene Type',
                        value: 'sceneType',
                        order: 6,
                    },
                    {
                        text: 'Tags',
                        value: 'tags',
                        order: 7,
                    },
                    {
                        text: 'User',
                        value: 'userName',
                        order: 8,
                    },
                    {
                        text: 'Scene Name',
                        value: 'sceneName',
                        order: 9,
                    },
                    {
                        text: 'Group',
                        value: 'group',
                        order: 10,
                    },
                    {
                        text: 'Progress',
                        value: 'progress',
                        filterable: false,
                        sortable: false,
                        order: 11,
                    },
                ]
            },
            selectedProcessSteps: [],
            playVideoDialog: {
                showDialog: false,
                currentVideoURL: null,
            },
            downloadFileDialog: {
                scanId: null,
                showDialog: false,
                fileInfo: [],
            },
            annotationDialog: {
                showDialog: false,
                iframeUrl: null,
            },
            editScanInfoDialog: {
                showDialog: false,
                comboBoxItems: [],
                editInfo: [],
            },
            alignScanDialog: {
                selectedScanInfo: [],
                showDialog: false,
            },
            queueDialog: {
                showDialog: false,
                queuedData: [],
                queuedInfo: {
                    queuedData: [],
                    isPaused: false,
                    isQueuedMenuLoading: false
                },
            },
            queuedInfo: {
                queuedData: [],
                isPaused: false,
                isQueuedMenuLoading: false
            },

            isReindexBtnLoading: false,


            isProcessBtnLoading: false,
            clearQueueDialog: {
                showClearQueueDialog: false,
                isClearQueueDialogLoading: false,
            },
            showQueuedMenu: false,

        }
    },
    methods: {
        openPlayVideoDialog(videoURL) {
            this.playVideoDialog.currentVideoURL = videoURL;
            this.playVideoDialog.showDialog = true;
        },
        openDownloadFilesDialog(scanId, fileNames) {
            this.downloadFileDialog.scanId = scanId;
            this.downloadFileDialog.fileInfo = fileNames;
            this.downloadFileDialog.showDialog = true;
        },
        openAnnotationDialog(scanId, format) {
            // this.annotationDialog.iframeUrl = 'https://aspis.cmpt.sfu.ca/stk-scenemotifs/scans/segment-annotator-single?condition=scannet-checked-manual&taskMode=fixup&modelId=multiscan.' + scanId + '&userId=' + localStorage.getItem('username');
            // this.annotationDialog.showDialog = true;
            window.open('http://spathi.cmpt.sfu.ca/scene-toolkit/model-viewer?extra&modelId=multiscan.' + scanId + '&userId=' + localStorage.getItem('username') + '&format=' + format, '_blank');
        },
        openEditScanInfoDialog(scans) {
            this.editScanInfoDialog.editInfo = []
            for (let scan of scans) {
                let oneScan = {
                    id: scan.id,
                    group: scan.group,
                    sceneName: scan.sceneName,
                    sceneType: scan.sceneType,
                    description: scan.description,
                    tags: scan.tags
                }
                this.editScanInfoDialog.editInfo.push(oneScan)
            }
            this.editScanInfoDialog.showDialog = true;
        },
        openAlignScanDialog() {
            this.alignScanDialog.selectedScanInfo = []
            for (let scan of this.tableInfo.selectedRows) {
                this.alignScanDialog.selectedScanInfo.push(
                    {id: scan.id, previewUrl: scan.previewUrl, alignThumbUrl: scan.alignmentThumbnail, sceneName: scan.sceneName, sceneType: scan.sceneType}
                );
            }
            this.alignScanDialog.showDialog = true;
        },
        getTableData(isReindexed, query) {
            this.tableInfo.isTableLoading = true;
            this.isReindexBtnLoading = true;
            let that = this;
            this.tableInfo.tableData = []
            this.editScanInfoDialog.comboBoxItems = []
            this.queuedInfo.queuedData = []
            this.$http.get('/scans/list', {params: query}).then(function (response) {
                for (let item of response.data.data) {
                    if (item.tags) {
                        for (let tag of item.tags) {
                            if (that.editScanInfoDialog.comboBoxItems.indexOf(tag) === -1) {
                                that.editScanInfoDialog.comboBoxItems.push(tag)
                            }
                        }
                    }
                    if (item.queueState && item.queueState.queued) {
                        that.queuedInfo.queuedData.push(item)
                    } else {
                        that.tableInfo.tableData.push(item)
                    }
                }
                that.tableInfo.isTableLoading = false;
                that.isReindexBtnLoading = false;
                if (isReindexed) {
                    that.showMessageBar("Reindex successfully", "success")
                }
            })
        },
        reindex() {
            this.tableInfo.isTableLoading = true;
            this.isReindexBtnLoading = true;
            this.tableInfo.tableData = []
            this.editScanInfoDialog.comboBoxItems = []
            let that = this;
            this.$http.get('/scans/index').then(function (response) {
                if (response.status === 200) {
                    that.getTableData(true)
                }
            })
        },
        submitOneProcess(id) {
            let that = this;
            this.isProcessBtnLoading = true;
            this.submitProcess(id).then(function (response) {
                if (response.status === 200) {
                    that.$http.get('/scans/index/' + id).then(function (response) {
                        that.selectedProcessSteps = []
                        that.isProcessBtnLoading = false;
                        if (response.status === 200) {
                            that.showMessageBar("Process task is being queued", "success")
                            that.getTableData()
                        } else {
                            that.showMessageBar("Error: Fail to process", "error")
                        }
                    })
                }
            })
        },
        submitAllProcesses() {
            let that = this;
            this.isProcessBtnLoading = true;
            let processes = []
            for (let scan of this.tableInfo.selectedRows) {
                processes.push(this.submitProcess(scan.id))
            }
            this.$http.all(processes).then(that.$http.spread((...response) => {
                let success = true;
                [...response].forEach((item) => {
                    if (item.status !== 200) {
                        success = false
                    }
                })
                that.selectedProcessSteps = []
                that.isProcessBtnLoading = false;
                if (success) {
                    that.showMessageBar("Process task is being queued", "success")
                    that.getTableData()
                } else {
                    that.showMessageBar("Error: Fail to process", "error")
                }
                that.cancelAllTableSelection()
            }))
        },
        submitProcess(id) {
            return this.$http.post('/queues/process/add', {
                scanId: id,
                overwrite: 1,
                actions: this.selectedProcessSteps
            })
        },
        submitRemoveProcess(id) {
            let that = this;
            this.$http.get('/queues/process/remove', {params: {scanId: id,}}).then(function (response) {
                if (response.status === 200) {

                    that.$http.get('/scans/index/' + id).then(function (response) {
                        console.log("????")
                        if (response.status === 200) {
                            that.showMessageBar("Process has been removed from the queue", "success")
                            that.getTableData()
                        } else {
                            that.showMessageBar("Error: Fail to remove the process", "error")
                        }
                        if(that.queueedCount === '0') {
                            that.showQueuedMenu = false;
                        }
                    })
                }
            })
        },
        submitClearQueue() {
            let that = this;
            this.clearQueueDialog.isClearQueueDialogLoading = true;
            this.$http.get('/queues/process/clear').then(function (response) {
                if (response.status === 200) {
                    that.clearQueueDialog.showClearQueueDialog = false;
                    that.clearQueueDialog.isClearQueueDialogLoading = false;
                    that.reindex();
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
                    that.showMessageBar("Pause the process queue successfully", "success")
                } else {
                    that.showMessageBar("Error: Fail to pause the process queue", "error")
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
                    that.showMessageBar("Resume the process queue successfully", "success")
                } else {
                    that.showMessageBar("Error: Fail to resume the process queue", "error")
                }
            })
        },
        getQueueStatus() {
            let that = this;
            this.$http.get('/queues/process/stats').then(function (response) {
                if (response.status === 200) {
                    that.queuedInfo.isPaused = response.data.isPaused
                    if(that.queuedInfo.size === 0) {
                        that.showQueuedMenu = false;
                    }
                }
            })
        },
        downloadCSV() {
            Downloader.download(['/projects/multiscan/staging/multiscan.csv']);
        },
        showMessageBar(message, type) {
            this.snackBarInfo.snackBarColor = type;
            this.snackBarInfo.snackBarText = message;
            this.snackBarInfo.showSnackBar = true;
        },
        submitOneEdit(id, key, value) {
            let that = this;
            let requestBody = {action: "edit", data: {}};
            requestBody.data[id] = {};
            requestBody.data[id][key] = value
            this.$http.post('/scans/edit', requestBody).then(function (response) {
                if (response.status === 200) {
                    that.showMessageBar("Edit successfully", "success");
                } else {
                    that.showMessageBar("Error: Failed to edit", "error");
                }
            });
        },
        loadColVisibility(reset) {
            this.tableInfo.tableHeaders = [];
            if (reset) {
                this.tableInfo.selectedCols = [
                    {
                        text: 'Video',
                        value: 'videoThumbnailUrl',
                        filterable: false,
                        sortable: false,
                        order: 1,
                    },
                    {
                        text: 'Preview',
                        value: 'previewUrl',
                        filterable: false,
                        sortable: false,
                        order: 2,
                    },
                    {
                        text: 'ID',
                        value: 'id',
                        order: 3,
                    },
                    {
                        text: 'Created At',
                        value: 'createdAt',
                        order: 4,
                    },
                    {
                        text: 'Scene Type',
                        value: 'sceneType',
                        order: 6,
                    },
                    {
                        text: 'Tags',
                        value: 'tags',
                        order: 7,
                    },
                    {
                        text: 'User',
                        value: 'userName',
                        order: 8,
                    },
                    {
                        text: 'Scene Name',
                        value: 'sceneName',
                        order: 9,
                    },
                    {
                        text: 'Group',
                        value: 'group',
                        order: 10,
                    },
                    {
                        text: 'Progress',
                        value: 'progress',
                        filterable: false,
                        sortable: false,
                        order: 11,
                    },
                ];
                sessionStorage.removeItem("cols_vis");
            }
            sessionStorage.setItem("cols_vis", JSON.stringify(this.tableInfo.selectedCols))
            for (let item of this.tableInfo.selectedCols) {
                this.tableInfo.tableHeaders.push(Object.assign({}, item));
            }
            this.tableInfo.tableHeaders.push({text: 'Actions', value: 'actions', filterable: false, sortable: false, order: 100})
            this.tableInfo.tableHeaders.push({text: '', value: 'data-table-expand', filterable: false, sortable: false, order: 101})
            this.tableInfo.tableHeaders.sort((a, b) => a.order - b.order);
        },
        cancelAllTableSelection() {
          this.tableInfo.selectedRows = []
        },

    },
    mounted() {
        if (sessionStorage.getItem("cols_vis")) {
            this.tableInfo.selectedCols = JSON.parse(sessionStorage.getItem("cols_vis"));
        }
        this.loadColVisibility();
        this.getTableData(false, this.$route.query);
    },
    computed: {
        queueedCount() {
            return this.queuedInfo.queuedData.length.toString();
        },
        isMultipleSelected() {
            return this.tableInfo.selectedRows.length > 0
        }
    },
    watch: {
        showQueuedMenu: function (newValue, old) {
            if (newValue && !old) {
                this.getQueueStatus();
            }
        },
        'tableInfo.selectedCols'() {
            this.loadColVisibility();
        },

        isMultipleSelected: function (newValue) {
            if (newValue) {
                this.tableInfo.tableHeaders
            }
        },

        '$route' () {
            this.$router.go(0);
        }
    }

}
</script>

<style scoped>

/deep/ .v-data-table > .v-data-table__wrapper tbody tr {
    box-shadow: none !important;
}

a {
    color: #0277BD !important;
    text-decoration: none;
}

a:hover {
    color: #0277BD;
    text-decoration: underline;
}


</style>


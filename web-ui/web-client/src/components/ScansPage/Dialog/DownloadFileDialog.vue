<template>
    <v-dialog v-model="showDialog" persistent width="600" scrollable>
        <v-card>
            <v-card-title style="opacity: 0.8">
                <span>Download Files</span>
                <v-spacer></v-spacer>
                <v-btn icon @click="close" :disabled="isLoading">
                    <v-icon>mdi-close</v-icon>
                </v-btn>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text>
                <v-list>
                    <template v-for="(item, index) in sortedFileInfo">
                        <div :key="item.name" class="py-3 d-flex align-center justify-center">
                            <div style="word-break: break-all;">
                                <span style="opacity: 0.8; font-size: 14px">{{ item.name }}</span><br/>
                                <span style="opacity: 0.7; font-size: 13px">Size: {{ sizeHelper(item.size) }}</span>
                            </div>
                            <v-spacer></v-spacer>
                            <v-checkbox color="primary" v-model="selectedFileNames" :value="item" class="ml-3"></v-checkbox>
                        </div>
                        <v-divider :key="index"></v-divider>
                    </template>
                </v-list>
            </v-card-text>
            <v-divider></v-divider>
            <v-card-actions class="pb-4 mx-1 mt-1">
                <span style="opacity: 0.7; font-size: 13px" class="mr-4">{{ selectedCount }} Selected<br/>Total Size: {{ selectedTotalSize }}</span>
                <v-spacer></v-spacer>
                <v-btn text @click="selectAll" :disabled="isLoading" color="primary">
                    Select All
                </v-btn>
                <v-btn color="primary" @click="downloadFiles" :loading="isLoading">
                    <v-icon small color="white" dark class="mr-1">mdi-download</v-icon>
                    Download
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
import Downloader from "@/utils/download";

export default {
    name: "DownloadDialog",
    props: {
        scanId: String,
        fileInfo: Array,
        showDialog: Boolean
    },
    model: {
        prop: 'showDialog',
        event: 'closeDialog'
    },
    computed: {
        selectedCount() {
            return this.selectedFileNames.length;
        },
        selectedTotalSize() {
            let totalSize = 0;
            this.selectedFileNames.forEach(fileName => totalSize += fileName.size)
            return this.sizeHelper(totalSize);
        },
        sortedFileInfo() {
            let tmp = this.fileInfo;
            tmp.sort((fileA, fileB) => fileA.name.split(".").slice(-1)[0].localeCompare(fileB.name.split(".").slice(-1)[0]));
            return tmp;
        }
    },
    data() {
        return {
            selectedFileNames: [],
            isLoading: false,
        }
    },
    methods: {
        close() {
            this.$emit('closeDialog', false);
            this.selectedFileNames = [];
        },
        downloadFiles() {
            this.isLoading = true;
            let urls = this.selectedFileNames.map(file => '/projects/multiscan/staging/' + this.scanId + '/' + file.name);
            Downloader.download(urls);
            close();
            this.isLoading = false;
        },
        sizeHelper(originalSize) {
            // From https://blog.csdn.net/z591102/article/details/106854329
            let size = "";
            if (originalSize < 1024) {
                size = originalSize.toFixed(2) + " B"
            } else if (originalSize < 1024 * 1024) {
                size = (originalSize / 1024).toFixed(2) + " KB"
            } else if (originalSize < 1024 * 1024 * 1024) {
                size = (originalSize / (1024 * 1024)).toFixed(2) + " MB"
            } else {
                size = (originalSize / (1024 * 1024 * 1024)).toFixed(2) + " GB"
            }
            let sizeStr = size;
            let index = sizeStr.indexOf(".");
            let dou = sizeStr.substr(index + 1, 2)
            if (dou === "00") {
                return sizeStr.substring(0, index) + sizeStr.substr(index + 3, 2)
            }
            return size;
        },
        selectAll() {
            if (this.selectedFileNames.length !== this.fileInfo.length) {
                this.selectedFileNames = this.fileInfo;
            } else {
                this.selectedFileNames = [];
            }

        }
    }
}
</script>

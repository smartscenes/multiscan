<template>
    <v-dialog v-model="showDialog" fullscreen hide-overlay transition="dialog-bottom-transition">
        <v-card>
            <v-toolbar dark color="primary" dense>
                <v-btn icon dark @click="tmpIframeUrl = ''; tempBtn = true">
                    <v-icon>mdi-close</v-icon>
                </v-btn>
                <v-toolbar-title>Annotation</v-toolbar-title>
            </v-toolbar>
            <iframe @load="close" ref="iframe" class="custom_iframe" :src="tmpIframeUrl"></iframe>
        </v-card>
    </v-dialog>
</template>

<script>
export default {
    name: "AnnotationDialog",
    props: {
        iframeUrl: String,
        showDialog: Boolean
    },
    model: {
        prop: 'showDialog',
        event: 'closeDialog'
    },
    data() {
        return {
            // TODO: fix the iframe exit problem, remove these two buttons
            tmpIframeUrl: null,
            tempBtn: false
        }
    },
    methods: {
        close() {
            if (this.showDialog && this.tempBtn) {
                this.tempBtn = false;
                this.$emit('closeDialog', false);
            }
        }
    },
    watch: {
        iframeUrl(newValue) {
            this.tmpIframeUrl = newValue;
        },
        showDialog(newValue) {
            if (newValue) {
                this.tmpIframeUrl = this.iframeUrl;
            }
        }
    }

}
</script>
<style scoped>
.custom_iframe {
    border: 0;
    width: 100%;
    height: calc(100% - 48px);
    display: block;
    position: absolute;
}
</style>

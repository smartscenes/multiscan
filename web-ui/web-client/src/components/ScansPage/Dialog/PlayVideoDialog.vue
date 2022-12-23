<template>
    <v-dialog width="unset" v-model="showDialog" dark overlay-opacity="0.6" @click:outside="close">
        <v-card style="line-height: 0" @mouseenter="showCloseBtn = true" @mouseleave="showCloseBtn = false">
            <v-btn absolute fab right icon @click="close" v-show="showCloseBtn"
                   style="width: 38px; height: 38px; right: 7px; top: 7px">
                <v-icon color="white">mdi-close</v-icon>
            </v-btn>
            <video autoplay :src="videoUrl" controls style="min-width: 800px"/>
        </v-card>
    </v-dialog>
</template>

<script>
export default {
    name: "VideoDialog",
    props: {
        videoUrl: String,
        showDialog: Boolean
    },
    model: {
        prop: 'showDialog',
        event: 'closeDialog'
    },
    data() {
        return {
            showCloseBtn: false,
        }
    },
    methods: {
        close() {
            this.$emit('closeDialog', false);
            this.showCloseBtn = false;
        }
    }
}
</script>


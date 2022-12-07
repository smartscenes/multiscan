<template>
    <v-dialog v-model="showDialog" persistent width="800">
        <v-card>
            <v-card-title style="opacity: 0.8">
                <span>Statistics</span>
                <v-spacer></v-spacer>
                <v-btn icon @click="close">
                    <v-icon>mdi-close</v-icon>
                </v-btn>
            </v-card-title>

            <v-card-text class="pa-7">
                <apexchart :options="chartOptions" :series="values" type="donut"></apexchart>
            </v-card-text>

        </v-card>
    </v-dialog>
</template>

<script>
import VueApexCharts from "vue-apexcharts";

export default {
    name: "ShowChartDialog",
    components: {
        'apexchart': VueApexCharts,
    },

    model: {
        prop: 'showDialog',
        event: 'closeDialog'
    },
    props: {
        showDialog: Boolean,
        chartOptions: Object,
        values: Array
    },
    methods: {
        close() {
            this.$emit('closeDialog', false);
        },
    },
    updated() {
        window.dispatchEvent(new Event('resize'))
    }
}
</script>

<style scoped>

</style>

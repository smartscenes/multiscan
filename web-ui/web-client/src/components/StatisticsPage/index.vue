<template>
    <v-container fluid class="d-flex justify-center">
        <v-card elevation="5" class="my-10 px-6 pt-5 pb-2" width="95%" max-width="1900">
            <!-- Table header -->
            <v-row class="pa-2" align="center">
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
            <!-- Table -->
            <v-data-table
                :loading="tableInfo.isTableLoading"
                :headers="tableInfo.tableHeaders"
                :items="tableInfo.tableData"
                :search="tableInfo.search"
                :footer-props="{'show-first-last-page': true, 'items-per-page-options': [20, 50, -1],
                'items-per-page-all-text': 'All', 'items-per-page-text': 'Items / Page'}">
                <template v-slot:item.actions="{item}">
                    <v-btn color="primary" :to="{name: 'ScansPage', query: {[tableInfo.queryKey]: item.key}}">
                        View
                    </v-btn>
                </template>
            </v-data-table>
        </v-card>
    </v-container>
</template>

<script>
export default {
    name: "StatisticsPage",
    data() {
        return {
            tableInfo: {
                tableHeaders: [],
                tableData: [],
                isTableLoading: true,
                search: '',
                title: '',
                queryKey: ''
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
            this.$http.get('/api/stats/scenes_names').then(function (response) {
                for (let item of response.data) {
                    that.tableInfo.tableData.push({key: item.sceneName, scansCount: item.scans})
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
                }
                that.tableInfo.isTableLoading = false;
            })
        },
        updatePage() {
            switch(this.$route.query.type) {
                case "sceneNames":
                    this.tableInfo.title = "Scene Names";
                    this.tableInfo.queryKey = "sceneName"
                    this.getSceneNamesTableData();
                    break;
                case "sceneTypes":
                    this.tableInfo.title = "Scene Types";
                    this.tableInfo.queryKey = "sceneType"
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
        }
    },
    mounted() {
        this.updatePage();
    },
    watch: {
        '$route' () {
            this.updatePage();
        }
    }
}
</script>

<style scoped>

</style>

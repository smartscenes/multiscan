<template>
    <v-app>
        <v-app-bar app color="primary" dense dark>
            <v-app-bar-title class="mr-4">MultiScan</v-app-bar-title>

<!--            <v-btn :to="{name: 'ScansPage'}" text class="mr-1">Scans</v-btn>-->
            <v-menu open-on-hover offset-y>
                <template v-slot:activator="{ on, attrs }">
                    <v-btn text v-bind="attrs" v-on="on">
                        Scans
                        <v-icon>mdi-menu-down</v-icon>
                    </v-btn>
                </template>

                <v-list>
                    <v-list-item @click="$router.push({name: 'ScansPage'}).catch(err => {})">All</v-list-item>
                    <v-list-item @click="$router.push({name: 'GroupViewPage', query: {type: item.value}}).catch(err => {})" v-for="item in views" :key="item.value">
                        {{item.name}}
                    </v-list-item>
                </v-list>
            </v-menu>

            <v-btn :to="{name: 'AnnotationsPage'}" text>Annotations</v-btn>


            <v-spacer></v-spacer>
            <v-toolbar-title class="text-body-1 mr-2">Hi! {{ username }}</v-toolbar-title>
        </v-app-bar>
        <v-main>
            <router-view></router-view>
        </v-main>
        <v-dialog v-model="showUsernameDialog" persistent width="330">
            <v-card>
                <v-card-text class="mb-0 pb-0 pt-5">
                    <p class="mb-4">Please enter your username:</p>
                    <v-text-field dense v-model="usernameInput" label="Username"
                                  :rules="[v => !!v || 'Username cannot be empty']" outlined
                                  maxlength="35"></v-text-field>
                </v-card-text>
                <v-card-actions class="mt-0 pt-0">
                    <v-spacer></v-spacer>
                    <v-btn color="primary" text @click="storeUsername">Confirm</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-app>
</template>

<script>

export default {
    name: 'App',
    data: () => ({
        showUsernameDialog: false,
        usernameInput: "",
        username: "",
        views: [
            {name: 'Scene Names', value:'sceneNames'},
            {name: 'Scene Types', value: 'sceneTypes'},
            {name: 'Devices', value: 'devices'},
            {name: 'Tags', value: 'tags'},
            {name: 'Users', value: 'users'}
        ]
    }),
    methods: {
        storeUsername() {
            localStorage.setItem("username", this.usernameInput);
            this.username = this.usernameInput;
            this.showUsernameDialog = false;
        }
    },
    mounted() {
        let localUsername = localStorage.getItem("username")
        if (!localUsername) {
            this.showUsernameDialog = true;
        } else {
            this.username = localUsername;
        }
    }
};
</script>
<style>

</style>

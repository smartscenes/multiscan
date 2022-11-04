<template>
    <v-dialog v-model="showDialog" persistent width="450">
        <v-card class="pb-1">
            <v-card-title style="opacity: 0.8">
                <span>{{isMultipleEdit ? "Edit Multiple Scans" : "Edit Scan"}}</span>
                <v-spacer></v-spacer>
                <v-btn icon @click="close" :disabled="isLoading">
                    <v-icon>mdi-close</v-icon>
                </v-btn>
            </v-card-title>
            <v-card-subtitle style="opacity: 0.5" v-if="isMultipleEdit" class="py-1">
                <span>Edit {{ editInfo.length }} Scans</span>
            </v-card-subtitle>
            <v-card-text>
                <v-form ref="editForm">
                    <v-radio-group dense v-model="formInfo.group" row mandatory label="Group:" :disabled="isLoading">
                        <v-radio label="Staging" value="staging"></v-radio>
                        <v-radio label="Checked" value="checked"></v-radio>
                        <v-radio label="Bad" value="bad"></v-radio>
                    </v-radio-group>
                    <v-combobox
                        :disabled="isLoading"
                        :items="comboBoxItems"
                        dense
                        clearable
                        deletable-chips
                        small-chips
                        multiple
                        label="Tags"
                        outlined
                        v-model="formInfo.tags">
                    </v-combobox>

                    <v-select
                        :disabled="isLoading"
                        v-model="formInfo.sceneType"
                        label="Scene Type"
                        :items="['Apartment', 'Bathroom', 'Bedroom / Hotel', 'Bookstore / Library', 'Classroom',
                                'Closet', 'Conference Room', 'Dining Room', 'Hallway', 'Kitchen', 'Living room / Lounge',
                                'Lobby', 'Office', 'Misc', 'Laundry Room', 'Storage/Basement/Garage', 'Mailboxes']"
                        dense
                        outlined
                    ></v-select>
                    <v-text-field label="Scene Name" dense outlined maxlength="35" :disabled="isLoading"
                                  v-model="formInfo.sceneName"></v-text-field>
                    <v-textarea outlined counter dense label="Scene Description" rows="3"
                                :disabled="isLoading" v-model="formInfo.description">
                    </v-textarea>
                </v-form>
            </v-card-text>
            <v-card-actions class="pb-3 mx-1">
                <v-spacer></v-spacer>
                <v-btn color="primary" @click="submitEdit" :loading="isLoading">
                    Submit
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
export default {
    name: "EditScanInfoDialog",
    model: {
        prop: 'showDialog',
        event: 'closeDialog'
    },
    props: {
        showDialog: Boolean,
        comboBoxItems: Array,
        editInfo: Array
    },
    data() {
        return {
            isLoading: false,
            editedInfo: [],
            formInfo: {
                group: "staging",
                tags: [],
                sceneName: "",
                sceneType: "",
                description: ""
            },
            isMultipleEdit: false,
        }
    },
    watch: {
        editInfo: {
            handler(newValue) {
                if (newValue.length === 1) {
                    this.isMultipleEdit = false;
                    this.formInfo.group = newValue[0].group;
                    this.formInfo.tags = newValue[0].tags;
                    this.formInfo.sceneName = newValue[0].sceneName;
                    this.formInfo.sceneType = newValue[0].sceneType;
                    this.formInfo.description = newValue[0].description;
                } else if (newValue.length > 1) {
                    let ifSceneNameMatch = true;
                    let ifSceneTypeMatch = true;
                    let ifDescriptionMatch = true;
                    let ifTagsMatch = true;
                    let ifGroupMatch = true;
                    for (let scan of newValue) {
                        if (scan.group !== newValue[0].group) {
                            ifGroupMatch = false;
                        }
                        if (scan.description !== newValue[0].description) {
                            ifDescriptionMatch = false;
                        }
                        if (scan.sceneName !== newValue[0].sceneName) {
                            ifSceneNameMatch = false;
                        }
                        if (scan.sceneType !== newValue[0].sceneType) {
                            ifSceneTypeMatch = false;
                        }
                        if (!this.compareArraySort(scan.tags, newValue[0].tags)) {
                            ifTagsMatch = false;
                        }
                    }
                    this.isMultipleEdit = true;
                    this.formInfo.group = ifGroupMatch ? newValue[0].group : "staging";
                    this.formInfo.tags = ifTagsMatch ? newValue[0].tags : [];
                    this.formInfo.sceneName = ifSceneNameMatch ? newValue[0].sceneName : "";
                    this.formInfo.sceneType = ifSceneTypeMatch ? newValue[0].sceneType : "";
                    this.formInfo.description = ifDescriptionMatch ? newValue[0].description : "";
                }
            },
            deep: true
        }
    },
    methods: {
        close() {
            this.$emit('closeDialog', false);
        },
        submitEdit() {
            this.isLoading = true;
            let that = this;
            let requestBody = {action: "edit", data: {}};
            for (let scan of this.editInfo) {
                requestBody.data[scan.id] = {
                    group: this.formInfo.group,
                    tags: this.formInfo.tags,
                    sceneName: this.formInfo.sceneName,
                    sceneType: this.formInfo.sceneType,
                    description: this.formInfo.description,
                };
            }

            this.$http.post('/scans/edit', requestBody).then(function (response) {
                that.close();
                that.isLoading = false;
                that.$refs.editForm.reset();
                if (response.status === 200) {
                    that.$parent.showMessageBar("Edit successfully", "success");
                    that.$parent.getTableData(false);
                } else {
                    that.$parent.showMessageBar("Error: Failed to edit", "error");
                }
                that.$parent.cancelAllTableSelection()
            });
        },
        compareArraySort(a1, a2){
            if ((!a1 && a2) || (a1 && ! a2)) return false;
            if (a1.length !== a2.length) return false;
            a1 = [].concat(a1);
            a2 = [].concat(a2);
            a1 = a1.sort();
            a2 = a2.sort();
            for (let i = 0, n = a1.length; i < n; i++) {
                if (a1[i] !== a2[i]) return false;
            }
            return true;
        }
    }
}
</script>

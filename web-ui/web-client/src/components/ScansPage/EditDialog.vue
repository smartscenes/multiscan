<template>
    <v-dialog v-model="showDialog" persistent width="400">
        <v-card class="pb-1">
            <v-card-title style="opacity: 0.8">
                <span>Edit Scan Information</span>
                <v-spacer></v-spacer>
                <v-btn icon @click="close" :disabled="isLoading">
                    <v-icon>mdi-close</v-icon>
                </v-btn>
            </v-card-title>
            <v-card-text>
                <v-form ref="editForm">
                    <v-radio-group dense v-model="editedInfo.group" row mandatory label="Group:" :disabled="isLoading">
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
                        v-model="editedInfo.tags">
                    </v-combobox>

                    <v-select
                        :disabled="isLoading"
                        v-model="editedInfo.sceneType"
                        label="Scene Type"
                        :items="['Apartment', 'Bathroom', 'Bedroom / Hotel', 'Bookstore / Library', 'Classroom',
                                'Closet', 'Conference Room', 'Dining Room', 'Hallway', 'Kitchen', 'Living room / Lounge',
                                'Lobby', 'Office', 'Misc', 'Laundry Room', 'Storage/Basement/Garage']"
                        dense
                        outlined
                    ></v-select>
                    <v-text-field label="Scene Name" dense outlined maxlength="35" :disabled="isLoading"
                                  v-model="editedInfo.sceneName"></v-text-field>
                    <v-textarea outlined counter dense label="Scene Description" rows="3"
                                :disabled="isLoading" v-model="editedInfo.description">
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
    name: "EditDialogView",
    model: {
        prop: 'showDialog',
        event: 'closeDialog'
    },
    props: {
        showDialog: Boolean,
        comboBoxItems: Array,
        editInfo: Object
    },
    data() {
        return {
            isLoading: false,
            editedInfo: {
                id: null,
                group: null,
                sceneName: null,
                sceneType: null,
                description: null,
                tags: [],
            },
        }
    },
    watch: {
        editInfo: {
            handler(newValue) {
                this.editedInfo.id = newValue.id;
                this.editedInfo.group = newValue.group;
                this.editedInfo.sceneName = newValue.sceneName;
                this.editedInfo.sceneType = newValue.sceneType;
                this.editedInfo.description = newValue.description;
                this.editedInfo.tags = newValue.tags;
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
            requestBody.data[this.editedInfo.id] = {
                group: this.editedInfo.group,
                tags: this.editedInfo.tags,
                sceneName: this.editedInfo.sceneName,
                sceneType: this.editedInfo.sceneType,
                description: this.editedInfo.description,
            };
            this.$http.post('/scans/edit', requestBody).then(function (response) {
                that.close();
                that.isLoading = false;
                that.$refs.editForm.reset();
                if (response.status === 200) {
                    that.$parent.showMessageBar("Edit successfully", "success");
                } else {
                    that.$parent.showMessageBar("Error: Failed to edit", "error");
                    that.$parent.getTableData(false);
                }
            });
        },
    }
}
</script>

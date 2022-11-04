<template>
    <v-tooltip right>
        <template v-slot:activator="{ on, attrs }">
            <v-progress-circular
                v-bind="attrs"
                v-on="on"
                style="font-size: 11px"
                :rotate="-90"
                :size="40"
                :width="5"
                :value="progressPercentage"
                :color="color">
                {{ progressPercentage }}%
            </v-progress-circular>
        </template>
        <div :key="item.name" v-for="item in stages">
            <span v-if="item.ok === undefined">{{ item.name }}</span>
            <span v-else-if="item.ok === true" style="color: #00E676">{{ item.name }} ✓</span>
            <span v-else style="color: #F44336">{{ item.name }} ×</span>
            <br/>
        </div>
    </v-tooltip>
</template>

<script>
export default {
    name: "ProgressCircle",
    props: {
        stages: Array
    },
    computed: {
        progressPercentage() {
            let total = this.stages.length;
            let okCount = 0;
            for (let stage of this.stages) {
                if (stage.ok && stage.ok === true) {
                    okCount += 1;
                }
            }
            return total === 0 ? 0 : Math.round(okCount / total * 100);
        },
        color() {
            for (let stage of this.stages) {
                if (stage.ok !== undefined && stage.ok === false) {
                    return "error"
                }
            }
            return "primary"
        }
    }
}
</script>

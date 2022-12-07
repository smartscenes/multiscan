<template>
    <iframe class="custom_iframe"
            src="https://aspis.cmpt.sfu.ca/stk-multiscan/multiscan/grouped?annotate=true"></iframe>
</template>

<script>
export default {
    name: "AnnotationsPage"
}
</script>

<style scoped>

.custom_iframe {
    border: 0;
    width: 100%;
    height: 100%;
    display: block;
    position: absolute;
}
</style>

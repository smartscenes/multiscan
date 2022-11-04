# MultiScan Web Front-end

## Introduction
This project uses [Vue.js](https://v2.vuejs.org/) v2 framework with [Axios](https://axios-http.com/) as the HTTP client. For UI design, it follows [Material Design](https://material.io/design) with [Vuetify](https://vuetifyjs.com/en/) framework.

## Configuration
For configs of [Vue.js](https://v2.vuejs.org/), please go to `vue.config.js`, for more custome configs, please refer to [Vue.js config reference](https://cli.vuejs.org/config/).

For configs of [Axios](https://axios-http.com/), please go to `src/axios/index.js`.

## Setup & Run
Make sure you have Node.js and npm installed first.

To install all dependencies, run:
```shell
npm install
```

To compile and run/hot-reload for development, run:
```shell
npm run serve
```
(Then the web runs on `localhost:8080` by default.)

To compile and minify for production, run:
```shell
npm run build
```
(It then outputs the compiled static webpages under `dist/`)

To lint and fix files, run:
```shell
npm run lint
```

## Web Page Endpoint
```
/scans                   # Main manage view
/group_view?             # Group view (1 param)
    (type=sceneNames)    # Group by scene names
    (type=sceneTypes)    # Group by scene types
    (type=devices)       # Group by scene devices
    (type=tags)          # Group by tags
    (type=users)         # Group by users
/annotations             # IFrame of annotations
```
(Note: to modify endpoints, please go to `src/router/index.js`)

## Code Structure

All source code is under `src/`, in high-level, code is organized in web pages, each web page corresponds to one endpoint as described in the [Web Page Endpoint](#web-page-endpoint) section:

- `src/ScansPage` (/scans)
- `src/GroupViewPage` (/group_view?)
- `src/AnnotationsPage` (/annotations)

Under each page folder, code is organized in lower-level components (e.g. dialog, progress indicator, etc.). Each `*.vue` file corresponds to one component in the current web page, each `index.vue` controls the whole web page. Specifically, each `*.vue` has three parts:

1. html (enclosed with `<template>` tag)
2. javascript (enclosed with `<script>` tag)
3. css (enclosed with `<style>` tag)

For more details, please refer to [Vue.js official guide](https://v2.vuejs.org/v2/guide/).

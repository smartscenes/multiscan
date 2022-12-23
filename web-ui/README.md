# Web UI

Web-UI is an interactive interface for providing an overview of staged scan data, managing scan data, controlling reconstruction process and mesh annotation pipeline. We use an indexing server, to index all the uploaded scans into a single csv file, which contains the ID and the info about scans. The indexed scans will be visualized in the web UI, and allows manual reprocessing the collected scans if needed. In the following sections we explain how users setup the web UI and how to interact with it.

## Web UI Server

The web UI [server](web-server) is the backend for the web UI, it provides the services end points for the web UI [client](web-client).

## Web UI Client

The web UI [client](web-client) is the frontend for the web UI, it provides the visualization and web browing functionality for the collected scans.
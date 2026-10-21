<!-- ai-generated: 0% - written by the course team -->
# grafana/dashboards/ - your dashboard JSON goes here

Export your dashboard as JSON into this directory, one `.json` file per dashboard. Your own Grafana loads every file
here (through `grafana/provisioning/dashboards/lab3.yml`), and the checker reads the same files: it never starts a
Grafana, it takes the query out of every panel and runs it on its own Prometheus (MONITORING-SPEC.md M-22 to
M-24, checks L3-CORE-6.01 to 6.04).

What the checker wants from the files here (subdirectories included):

- at least one Grafana dashboard JSON: the dashboard object with its `panels` list, or an export of the form
  `{"dashboard": {...}}`;
- **no library panels**: a library panel keeps its query outside the file, so the checker cannot run it;
- at least three panels with queries (the `expr` of each panel's `targets`), one of them a `histogram_quantile`
  over `http_server_request_duration_seconds_bucket`;
- every query parses and runs on the checker's Prometheus after Grafana's variables are replaced
  (`$__rate_interval` becomes `1m`; the whole table is in M-23), and every metric it selects by name exists
  there: scraped from `svcdesk`, or made by the recording rules in your `prometheus/alerts.yml`.

How to work: build the panels in your Grafana on a new dashboard (a provisioned one cannot be saved from the UI),
pointed at the provisioned datasource, uid `prometheus`; then open the dashboard's export and save its JSON here.
Leave off the option that prepares an export for another Grafana instance: it replaces the datasource with an
input that file provisioning does not fill in. Within ten seconds Grafana shows the file's version in the folder
`svcdesk`. You need not save the draft in Grafana at all; if you did, delete it, because two dashboards with the
same uid get in each other's way.

This README is not a dashboard, and the checker ignores it.

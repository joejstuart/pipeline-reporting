#!/usr/bin/env python3

import pipeline_reporting.influxdbQuery as metrics
import re
import datetime
import json
import os


# define the html output
def html_output(job_name, job_results, measurement):
    page_content = list()
    today = datetime.datetime.today()
    week_ago = today - datetime.timedelta(days=7)
    today = int(today.timestamp()) * 1000
    week_ago = int(week_ago.timestamp()) * 1000
    all_pkgs_dashboard = all_pkgs_url.format(measurement, week_ago, today)
    page_content.append("<div style='width: 50%; border-bottom: 1px solid #A09B9A; padding: 5px;'>")
    page_content.append("<h1><a style='color: #000000; text-decoration: none;' href='{}'>{}</a></h1>".format(all_pkgs_dashboard, job_name))

    if not len(job_results):
        page_content.append('<br />')
        page_content.append('<div>')
        page_content.append("No builds for this week.")
        page_content.append('</div>')

    for result in job_results:
        page_content.append("<h5>{}</h5>".format(result))
        for build_results in job_results[result]:
            dashboard_url = grafana_url.format(week_ago, today, measurement, build_results[1])
            job_url = jenkins_url.format(job_name.replace('_', '-'), build_results[2])
            influx_time = None
            for time_fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ'):
                try:
                    influx_time = datetime.datetime.strptime(build_results[0], time_fmt)
                except ValueError:
                    pass

                if influx_time:
                    break

            if not influx_time:
                continue

            fmt_time = influx_time.strftime('%m-%d-%y %H:%M:%S')
            page_content.append('<div>')
            page_content.append("<div style='padding-right: 5px; display:inline-block;'>")
            page_content.append("{}:".format(fmt_time))
            page_content.append('</div>')
            page_content.append("<div style='width: 150px; padding-right: 5px; display:inline-block;'>")
            page_content.append("<a href='{}'>{}</a>".format(job_url, build_results[1]))
            page_content.append('</div>')
            page_content.append("<div style='display:inline-block;'>")
            page_content.append("<a href='{}'>Dashboard</a>".format(dashboard_url))
            page_content.append('</div>')
            page_content.append('</div>')

    page_content.append('</div>')
    page_content.append('<br />')

    return ''.join(page_content)


def text_output(job_name, job_results):
    pass


pipeline = os.environ['PIPELINE']

pipeline_data = {
    'Fedora': {
        'jenkins_url': "https://jenkins-continuous-infra.apps.ci.centos.org/view/Fedora%20All%20Packages%20Pipeline/job/{}/{}/console",
        'influxdb_url': 'influxdb-continuous-infra.apps.ci.centos.org',
        'build_prefix': 'Fedora_All_Packages_Pipeline',
        'title': 'Fedora Pipeline',
        'grafana_all_pkgs': 'http://grafana-continuous-infra.apps.ci.centos.org/d/gJYUENmmk/upstream-fedora-pipeline?orgId=1&amp;var-measurement={}&amp;from={}&amp;to={}',
        'grafana_url': 'http://grafana-continuous-infra.apps.ci.centos.org/d/-esp4Gvmz/fedora-packages?orgId=1&amp;from={}&amp;to={}&amp;var-pipeline={}&amp;var-package={}'
    },
    'RHEL': {
        'jenkins_url': "",
        'influxdb_url': '',
        'build_prefix': '',
        'title': ''
    }

}

jenkins_url = None
influxdb = None
build_prefix = None
page_title = None
grafana_url = None
all_pkgs_url = None

try:
    jenkins_url = pipeline_data[pipeline]['jenkins_url']
    influxdb_url = pipeline_data[pipeline]['influxdb_url']
    build_prefix = pipeline_data[pipeline]['build_prefix']
    page_title = pipeline_data[pipeline]['title']
    grafana_url = pipeline_data[pipeline]['grafana_url']
    all_pkgs_url = pipeline_data[pipeline]['grafana_all_pkgs']
except KeyError:
    raise Exception('Invalid pipeline name')

influxdb = metrics.InfluxDB(influxdb_url, build_prefix)

content = []
for measurement in influxdb.measurements():
    if (not re.search('.*trigger.*', measurement)) and (not re.search('.*stage.*', measurement)):
        job_name = influxdb.strip_prefix(measurement)
        if job_name:
            job_results = influxdb.all_job_data(measurement)
            content.append(html_output(job_name, job_results, measurement))

confluence = metrics.Confluence(os.environ['CONFLUENCE_URL'])
title = "%s: %s" % (page_title, datetime.date.today())
resp = confluence.create_page(60659866, title, ''.join(content))

print(resp.status_code)
print(json.dumps(resp.json(), indent=4, sort_keys=True))

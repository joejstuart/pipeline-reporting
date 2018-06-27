from influxdb import InfluxDBClient
import collections
import os
import requests
import re
import json


class InfluxDB:

    def __init__(self, server, build_prefix, db='db0'):
        user = os.environ['INFLUXDB_USER']
        password = os.environ['INFLUXDB_PASSWORD']

        if not (user and password):
            raise Exception('Username/Password not set')

        self.client = InfluxDBClient(server, '80', user, password, db)
        self.build_prefix = build_prefix

    def measurements(self):
        measurements = []
        query = 'SHOW measurements WHERE build_result =~ /.*/'

        for values in self.client.query(query).raw['series'][0]['values']:
            measurement = values[0]
            if measurement != 'jenkins_data':
                measurements.append(measurement)

        return measurements

    def strip_prefix(self, measurement):
        # Strip the measurement prefix while making sure it is prefixed
        # with self.build_prefix
        m = re.search("%s_(.*)" % self.build_prefix, measurement)

        if m:
            return m.group(1)
        else:
            print(measurement)

    def failed_builds(self):
        return self.job_data_build_result('FAILURE')

    def failed_package_tests(self):
        return self.job_data_build_result('UNSTABLE')

    def successful_packages(self):
        return self.job_data_build_result('SUCCESS')

    def job_data_build_result(self, build_result):
        package_results = collections.defaultdict(list)

        for measurement in self.measurements():
            query = "SELECT * FROM %s WHERE build_result = '%s' AND time > now() - 7d" % (measurement, build_result)
            for results in self.client.query(query):
                for result in results:
                    job_name = self.strip_prefix(measurement)
                    package_results[job_name].append(','.join((result['time'], result['package_name'])))

        for package in package_results:
            print(package)
            print('\n'.join(package_results[package]))
            print('\n')

    def all_job_data(self, measurement):
        package_results = collections.defaultdict(list)
        query = "SELECT * FROM %s WHERE time > now() - 7d" % measurement

        for results in self.client.query(query):
            for result in results:
                package_results[result['build_result']].append((result['time'], result['package_name'],
                                                                str(result['build_number'])))

        return package_results


class Confluence:

    def __init__(self, rest_url):
        user = os.environ['CONFLUENCE_USER']
        password = os.environ['CONFLUENCE_PASSWORD']

        if not (user and password):
            raise Exception('Username/Password not set')

        self.headers = {'Content-Type': 'application/json'}
        self.auth = (user, password)
        self.rest_url = rest_url

    def create_page(self, parent_page, title, content):
        page_template = {'type': 'page', 'title': None, 'ancestors': [{'id': parent_page}], 'space': {'key': 'CONTRA'}, 'body': {'storage': {'value': None, 'representation': 'storage'}}}
        page_template['title'] = title
        page_template['body']['storage']['value'] = content

        return requests.post(self.rest_url, json.dumps(page_template),
                             auth=self.auth, verify=False, headers=self.headers)

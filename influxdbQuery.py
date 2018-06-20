from influxdb import InfluxDBClient
import collections
import os
import requests


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
        prefix_len = len(self.build_prefix) + 1
        return measurement[prefix_len:]

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

        self.auth = requests.auth.HTTPBasicAuth(user, password)
        self.rest_url = rest_url

    def update_page(self, content):
        return requests.post(self.rest_url, content, auth=self.auth)


#print("Failed Builds")
#influxdb.failed_builds()
#print('\n\n')

#print("Failed Package Tests")
#influxdb.failed_package_tests()
#print('\n\n')

#print("Successful Builds")
#influxdb.successful_packages()
#print('\n\n')


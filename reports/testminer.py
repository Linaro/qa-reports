import ast
import base64
import csv
import json
import os
import requests
import shutil
import subprocess
import xmlrpclib
import yaml
from copy import deepcopy

from subprocess import Popen, PIPE, STDOUT

try:
    from subprocess import DEVNULL # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')


class TestSystem(object):
    def test_results_available(self, job_id):
        return False

    def get_test_job_status(self, job_id):
        return None

    def get_test_job_results(self, job_id):
        #return dict(boot=[], test=[])
        return []

    def get_test_job_details(self, job_id):
        """
        returns test job metadata, for example device type
        the tests were run on
        """
        return {}

    def get_job_url(self, job_id):
        return None

    def cleanup(self):
        return None

    def get_result_class_name(self, job_id):
        return None

    def get_result_data(self, job_id):
        return None, None

    @staticmethod
    def reduce_test_results(test_result_list):
        return None


class LavaServerException(Exception):
    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return self.args

    def __repr__(self):
        return self.args



class GenericLavaTestSystem(TestSystem):
    XMLRPC = 'RPC2/'
    BUNDLESTREAMS = 'dashboard/streams'
    JOB = 'scheduler/job'
    def __init__(self, base_url, username=None, password=None, repo_prefix=None):
        self.url = base_url
        self.username = username # API username
        self.password = password # API token
        self.xmlrpc_url = base_url + LavaTestSystem.XMLRPC
        self.stream_url = base_url + LavaTestSystem.BUNDLESTREAMS
        self._url = base_url + LavaTestSystem.JOB
        self.result_data = None

    def test_results_available(self, job_id):
        status = self.call_xmlrpc('scheduler.job_status', job_id)
        return 'bundle_sha1' in status and len(status['bundle_sha1']) > 0

    def get_job_url(self, job_id):
        return "%s%s/%s" % (self.url, LavaTestSystem.JOB, job_id)

    def get_test_job_status(self, job_id):
        result = self.call_xmlrpc("scheduler.job_status", job_id)
        return result['job_status']

    def get_test_job_details(self, job_id):
        """
        returns test job metadata, for example device type
        the tests were run on
        """
        details = dict(testertype="lava")
        status = self.call_xmlrpc('scheduler.job_status', job_id)
        if 'bundle_sha1' in status:
            details.update({"bundle": status['bundle_sha1']})
        content = self.call_xmlrpc('scheduler.job_details', job_id)
        definition = json.loads(content['definition'])
        if content['multinode_definition']:
            definition = json.loads(content['multinode_definition'])
        details.update({"definition": str(json.dumps(definition))})
        for action in definition['actions']:
            if action['command'].startswith("submit_results"):
                if 'stream' in action['parameters'].keys():
                    details.update({"bundlestream": action['parameters']['stream']})
            if 'metadata' in action.keys():
                details.update(action['metadata'])
        return details

    def get_result_class_name(self, job_id):
        content = self.call_xmlrpc('scheduler.job_details', job_id)
        definition = json.loads(content['definition'])
        for action in definition['actions']:
            if action['command'] == "lava_test_shell":
                if 'testdef_repos' in action['parameters'].keys():
                    for test_repo in action['parameters']['testdef_repos']:
                        if test_repo['testdef'].endswith("art-microbenchmarks.yaml"):
                            return "ArtMicrobenchmarksTestResults"
                        if test_repo['testdef'].endswith("wa2host_postprocessing.yaml"):
                            return "ArtWATestResults"
        return "GenericLavaTestSystem"

    def call_xmlrpc(self, method_name, *method_params):
        payload = xmlrpclib.dumps((method_params), method_name)

        response = requests.request('POST', self.xmlrpc_url,
                                    data = payload,
                                    headers = {'Content-Type': 'application/xml'},
                                    auth = (self.username, self.password),
                                    timeout = 100,
                                    stream = False)

        if response.status_code == 200:
            try:
                result = xmlrpclib.loads(response.content)[0][0]
                return result
            except xmlrpclib.Fault as e:
                message = "Fault code: %d, Fault string: %s\n %s" % (
                    e.faultCode, e.faultString, payload)
                raise LavaServerException(message)
        else:
            raise LavaServerException(response.status_code)


class LavaTestSystem(GenericLavaTestSystem):
    REPO_HOME = "/tmp/repos" # change it to cofigurable parameter
    def __init__(self, base_url, username=None, password=None, repo_prefix=None):
        self.repo_prefix = repo_prefix
        self.repo_dirs = set([])
        #self.repo_home = os.path.join(os.getcwd(), LavaTestSystem.REPO_HOME)
        self.repo_home = LavaTestSystem.REPO_HOME
        if repo_prefix:
            self.repo_home = os.path.join(
                LavaTestSystem.REPO_HOME + "/" + repo_prefix)
        super(LavaTestSystem, self).__init__(base_url, username, password)

    def cleanup(self):
        for repo_dir in self.repo_dirs:
            shutil.rmtree(repo_dir)
        if self.repo_prefix and os.path.exists(self.repo_home):
            shutil.rmtree(self.repo_home)

    def get_test_job_results(self, job_id):
        return None

    def _extract_test_repos(self, testdef_repo_list):
        return_list = []
        for index, repo in enumerate(testdef_repo_list):
            if "git-repo" in repo.keys():
                return_list.append(repo)
                self._clone_test_git_repo(repo['git-repo'])
                #print "\t\t\tTest repository: %s" % repo['git-repo']
                #print "\t\t\tTest file: %s" % repo['testdef']
                #if "parameters" in repo.keys():
                #    #print "\t\t\tParameters:"
                #    for param_key, param_value in repo["parameters"].iteritems():
                #        #print "\t\t\t\t%s: %s" % (param_key, param_value)
        return return_list

    def _escape_url(self, url):
        return url.replace(":", "_").replace("/", "_")

    def _clone_test_git_repo(self, url):
        url_escaped = self._escape_url(url)
        if not os.path.exists(self.repo_home):
            os.makedirs(self.repo_home)
        os.chdir(self.repo_home)
        if not os.path.exists(os.path.join(os.getcwd(), url_escaped)) \
            or not os.path.isdir(os.path.join(os.getcwd(), url_escaped)):
            subprocess.call(['git', 'clone', url, url_escaped], stdout=DEVNULL, stderr=subprocess.STDOUT)
        return_path = os.path.join(os.getcwd(), url_escaped)
        #os.chdir("..")
        return return_path

    def _git_checkout_and_reset(self, commit_id):
        subprocess.call(['git', 'checkout', 'master'], stdout=DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(['git', 'reset', '--hard'], stdout=DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(['git', 'pull', 'origin', 'master'], stdout=DEVNULL, stderr=subprocess.STDOUT)
        subprocess.call(['git', 'checkout', commit_id], stdout=DEVNULL, stderr=subprocess.STDOUT)

    def _find_test_file_name(self, repo_type, test_metadata, repo_url, commit_id):
        if repo_type.upper() == 'GIT':
            return self._git_find_test_file_name(test_metadata, repo_url, commit_id)

    def _git_find_test_file_name(self, test_metadata, git_repo_url, commit_id):
        os.chdir(self.repo_home)
        url_escaped = self._escape_url(git_repo_url)
        file_name_list = []
        if os.path.exists(os.path.join(os.getcwd(),url_escaped)) \
            and os.path.isdir(os.path.join(os.getcwd(),url_escaped)):
            self.repo_dirs.add(os.path.join(os.getcwd(),url_escaped))
            os.chdir(url_escaped)
            #base_path = os.getcwd()
            self._git_checkout_and_reset(commit_id)
            for root, dirs, files in os.walk('.'):
                for name in files:
                    if name.endswith("yaml"):
                        # TODO check for symlink?
                        f = open(os.path.join(os.getcwd(), root, name), 'r')
                        y = yaml.load(f.read())
                        f.close()
                        # assume tests are in Linaro format
                        #if test_medatada['name'] == y['metadata']['name'] \
                        #        and test_medatada['os'] = y['metadata']['os']:
                        if test_metadata['name'] == y['metadata']['name'] \
                            and set(test_metadata['os'].split(",")) == set(y['metadata']['os']):
                            #os.chdir("../../")
                            if len(root) > 1:
                                #return root.lstrip("./") + "/" + name
                                file_name_list.append(root.lstrip("./") + "/" + name)
                            else:
                                #return name
                                file_name_list.append(name)
        #    os.chdir("..")
        #os.chdir("..")
        #return None
        return file_name_list

    def _match_results_to_definition(
            self,
            defined_tests,
            test_location_type,
            test_location_url,
            #test_file_name,
            test_file_name_list,
            test_params,
            test_version,
            test_results):
        # update defined_tests dictionary with test results
        for result in test_results:
            if 'attachments' in result.keys():
                del result['attachments']
        for test_dict in defined_tests:
            if test_location_type.upper() == 'GIT':
                if 'git-repo' in test_dict.keys():
                    if test_dict['git-repo'] == test_location_url \
                        and test_dict['testdef'] in test_file_name_list:
                        #and test_dict['testdef'] == test_file_name:
                        # check parameters match
                        # Warning! There is no way to distinguish between
                        # identical test shells in the same job
                        # if the test is run multiple times in the same job
                        # there should be a parameter allowing to match the results
                        # to the requested test (even if the parameter is not used
                        # in the test).

                        test_file_name = test_dict['testdef']
                        if test_params:
                            f = open(
                                os.path.join(
                                    self.repo_home,
                                    self._escape_url(test_location_url),
                                    test_file_name)
                                )
                            y = yaml.load(f.read())
                            f.close()

                            default_parameters = y['params']
                            if 'parameters' in test_dict:
                                default_parameters.update(test_dict['parameters'])
                            if test_params == default_parameters:
                                # this is likely match
                                # so append test results here
                                test_dict.update({'results': test_results})
                                test_dict.update({'version': test_version})
                        else:
                            # no test_params, now what?!
                            if 'parameters' not in test_dict:
                                # looks like a match
                                test_dict.update({'results': test_results})
                                test_dict.update({'version': test_version})

    def assign_indexed_result(self, defined_tests, index, result):
        test_index = 0
        for test_key, test_dict in defined_tests.iteritems():
            for testdef_key, testdef_dict in test_dict.iteritems():
                if test_index == index:
                    defined_tests[test_key][testdef_key]['boot'] = deepcopy(result)
                else:
                    test_index = test_index + 1

    def match_lava_to_definition(
            self,
            defined_tests,
            lava_result_list):
        # match tests from 'lava' to corresponding shell if possible
        test_shell_found = False
        test_shell_index = 0
        lava_results = {}
        for result in lava_result_list:
            if not test_shell_found:
                if result['test_case_id'] == 'lava_test_shell':
                    test_shell_found = True
            else:
                if result['test_case_id'] == 'lava_test_shell':
                    self.assign_indexed_result(defined_tests, test_shell_index, lava_results)
                    lava_results = {}
                    test_shell_index = test_shell_index + 1
            lava_results[result['test_case_id']] = result
        self.assign_indexed_result(defined_tests, test_shell_index, lava_results)


    def get_test_job_results(self, job_id):
        """
        returns test job results
        """
        status = self.call_xmlrpc('scheduler.job_status', job_id)
        sha1 = None
        if 'bundle_sha1' in status:
            sha1 = status['bundle_sha1']
            #print "\t\tBundle SHA1: %s" % sha1
        content = self.call_xmlrpc('scheduler.job_details', job_id)
        #print "\t\tRequested device type: %s" % content['requested_device_type_id']
        definition = json.loads(content['definition'])
        if content['multinode_definition']:
            definition = json.loads(content['multinode_definition'])
        stream = None
        defined_tests = []
        all_tests = dict(boot=[], test=defined_tests)
        for action in definition['actions']:
            if action['command'] == "submit_results":
                stream = action['parameters']['stream']
            if action['command'] == "lava_test_shell":
                if 'testdef_repos' in action['parameters'].keys():
                    extracted_tests = self._extract_test_repos(action['parameters']['testdef_repos'])
                    for test in extracted_tests: defined_tests.append(test)

        if sha1:
            result_bundle = self.call_xmlrpc('dashboard.get', sha1)
            bundle = json.loads(result_bundle['content'])
            for run in iter(bundle['test_runs']):
                test_results = run['test_results']
                if run['test_id'] != 'lava':
                    meta_data = run['testdef_metadata']
                    test_location_type = meta_data['location']
                    test_location_url = meta_data['url']
                    test_version = meta_data['version']
                    test_name = meta_data['name']
                    #test_file_name = self._find_test_file_name(test_location_type, meta_data, test_location_url, test_version)
                    test_file_name_list = self._find_test_file_name(test_location_type, meta_data, test_location_url, test_version)
                    test_results = run['test_results']
                    if 'software_context' in run.keys():
                        test_source = None
                        for source in run['software_context']['sources']:
                            if source['branch_url'] == test_location_url \
                                and source['branch_revision'] == test_version:
                                test_source = source
                        test_params = {}
                        if len(test_source['default_params']) > 0:
                            # this means test_source returned empty string
                            test_params = ast.literal_eval(test_source['default_params'])
                        if len(test_source['test_params']) > 0:
                            test_params.update(ast.literal_eval(test_source['test_params']))
                        # identify matching defined test
                        self._match_results_to_definition(
                                defined_tests,
                                test_location_type,
                                test_location_url,
                                #test_file_name,
                                test_file_name_list,
                                test_params,
                                test_version,
                                test_results)
                else:
                    # process lava results
                    # these should include boot time, boot success etc.
                    # since it's almost impossible to match the tess
                    # to corresponding actions (especially in multinode)
                    # average values are added to the defined_tests
                    # as additional test with name 'boot'
                    boot_result = 'pass'
                    boot_reason = ''
                    boot_time = 0.0 #average
                    boot_samples = 0
                    userspace_boot_time = 0.0 #average
                    userspace_boot_samples = 0
                    android_userspace_boot_time = 0.0 #average
                    android_userspace_boot_samples = 0
                    test = {
                        'name': 'boot',
                        'target': run['attributes']['target'],
                        'boot_time': boot_time,
                        'boot_attempts': boot_samples}
                    for result in test_results:
                        if result['test_case_id'] == 'test_kernel_boot_time':
                            boot_time = boot_time + float(result['measurement'])
                            boot_samples = boot_samples + 1
                            if result['result'] == 'fail':
                                boot_result = 'fail'
                                boot_reason = 'kernel boot failed'
                        if result['test_case_id'] == 'test_userspace_home_screen_boot_time':
                            android_userspace_boot_time = android_userspace_boot_time + float(result['measurement'])
                            android_userspace_boot_samples = android_userspace_boot_samples + 1
                            if result['result'] == 'fail':
                                boot_result = 'fail'
                                boot_reason = 'android userspace home screen boot failed'
                        if result['test_case_id'] == 'test_userspace_boot_time':
                            userspace_boot_time = userspace_boot_time + float(result['measurement'])
                            userspace_boot_samples = userspace_boot_samples + 1
                            if result['result'] == 'fail':
                                boot_result = 'fail'
                                boot_reason = 'userspace boot failed'
                        if result['test_case_id'] == 'dummy_deploy':
                            if result['result'] == 'pass':
                                boot_samples = 1
                    if boot_time > 0:
                        boot_time = boot_time/float(boot_samples)
                        test.update({
                            'boot_time': boot_time,
                            'boot_attempts': boot_samples
                            })
                    if android_userspace_boot_time > 0:
                        android_userspace_boot_time = android_userspace_boot_time/float(android_userspace_boot_samples)
                        test.update({
                            'android_userspace_boot_time': android_userspace_boot_time,
                            'android_userspace_boot_attempts': android_userspace_boot_samples
                            })
                    if userspace_boot_time > 0:
                        userspace_boot_time = userspace_boot_time/float(userspace_boot_samples)
                        test.update({
                            'userspace_boot_time': userspace_boot_time,
                            'userspace_boot_attempts': userspace_boot_samples
                            })
                    if boot_samples == 0:
                        boot_result = 'fail'
                        boot_reason = 'No boot attempts found'
                    test['result'] = boot_result
                    test['reason'] = boot_reason
                    all_tests['boot'].append(test)
            for test in all_tests['test']:
                overall_result = 'pass'
                reason_list = []
                tests_run = 0
                tests_pass = 0
                tests_skip = 0
                tests_fail = 0
                if 'results' in test.keys():
                    tests_run = len(test['results'])
                    for result in test['results']:
                        if result['result'] == 'fail':
                            overall_result = 'fail'
                            reason_list.append(result['test_case_id'])
                            tests_fail = tests_fail + 1
                        elif result['result'] == 'skip':
                            tests_skip = tests_skip + 1
                        elif result['result'] == 'pass':
                            tests_pass = tests_pass + 1
                else:
                    overall_result = 'fail'
                    reason_list.append('Test Results Missing!')
                test['result'] = overall_result
                test['reason'] = ",".join(reason_list)
                test['total_count'] = tests_run
                test['pass_count'] = tests_pass
                test['skip_count'] = tests_skip
                test['fail_count'] = tests_fail

        return all_tests

    @staticmethod
    def reduce_test_results(test_result_list):
        if len(test_result_list) < 1:
            return None
        test_result_set = set(test_result_list)
        if len(test_result_set) == 1:
            return test_result_set.pop()
        else:
            if 'red' in test_result_set:
                return 'red'
            if 'yellow' in test_result_set:
                return 'yellow'
            if 'green' in test_result_set: # in case there is green and N/A
                return 'green'
        return None

class ArtMicrobenchmarksTestResults(LavaTestSystem):
    def get_test_job_results(self, test_job_id):

        status = self.call_xmlrpc('scheduler.job_status', test_job_id)

        if not ('bundle_sha1' in status and status['bundle_sha1']):
            return []

        test_result_list = []

        sha1 = status['bundle_sha1']
        result_bundle = self.call_xmlrpc('dashboard.get', sha1)
        bundle = json.loads(result_bundle['content'])

        target = [t for t in bundle['test_runs'] if t['test_id'] == 'multinode-target']
        if target:
            target = iter(target).next()
        else:
            return test_result_list
        host = [t for t in bundle['test_runs'] if t['test_id'] == 'art-microbenchmarks']
        if host:
            host = iter(host).next()
        else:
            return test_result_list
        src = (s for s in host['software_context']['sources'] if 'test_params' in s).next()
        # This is an art-microbenchmarks test
        # The test name and test results are in the attachmented pkl file
        # get test results for the attachment
        test_mode = ast.literal_eval(src['test_params'])['MODE']
        json_attachments = [a['content'] for a in host['attachments'] if a['pathname'].endswith('json')]

        if not json_attachments:
            #fixme retrieve test results from LAVA results
            #if 'test_results' not in host.keys():
            #    return []
            #test_result_dict = {}
            #for test in host['test_results']:
            #    if 'measurement' in test.keys():
            #        benchmark, test_case_name = test['test_case_id'].split("-", 1)
            #        if benchmark in test_result_dict.keys():
            #            test_result = test_result_dict[benchmark]
            #            test_result['subscore'].append(
            #                    {"name": test_case_name,
            #                     "measurement": test['measurement']
            #                    })
            #        else:
            #            test_result = {}
            #            test_result['board'] = target['attributes']['target']
            #            test_result['board_config'] = target['attributes']['target']
            #            # benchmark iteration
            #            test_result['benchmark_name'] = benchmark
            #            test_result['subscore'] = [
            #                    {"name": test_case_name,
            #                     "measurement": test['measurement']
            #                    }]
            #            test_result_dict[benchmark] = test_result
            #return [value for key, value in test_result_dict.iteritems()]
            return []


        json_text = base64.b64decode(json_attachments[0])
        # save json file locally
        #with open(self.result_file_name + "_" + str(test_mode) + ".json", "w") as json_file:
        #    json_file.write(json_text)
        test_result_dict = json.loads(json_text)
        if 'benchmarks' in test_result_dict.keys():
            test_result_dict = test_result_dict['benchmarks']
        # Key Format: benchmarks/micro/<BENCHMARK_NAME>.<SUBSCORE>
        # Extract and unique them to form a benchmark name list
        test_result_keys = list(bn.split('/')[-1].split('.')[0] for bn in test_result_dict.keys())
        benchmark_list   = list(set(test_result_keys))
        for benchmark in benchmark_list:
            test_result = {}
            test_result['board'] = target['attributes']['target']
            test_result['board_config'] = target['attributes']['target']
            # benchmark iteration
            test_result['benchmark_name'] = benchmark
            test_result['subscore'] = []
            key_word = "/%s." % benchmark
            tests = ((k, test_result_dict[k]) for k in test_result_dict.keys() if k.find(key_word) > 0)
            for test in tests:
                # subscore iteration
                subscore = "%s_%s" % (test[0].split('.')[-1], test_mode)
                for i in test[1]:
                    test_case = { "name": subscore,
                                  "measurement": i }
                    test_result['subscore'].append(test_case)

            test_result_list.append(test_result)
        return test_result_list

    def get_result_data(self, test_job_id):
        status = self.call_xmlrpc('scheduler.job_status', test_job_id)

        if not ('bundle_sha1' in status and status['bundle_sha1']):
            return (None, None)

        sha1 = status['bundle_sha1']
        result_bundle = self.call_xmlrpc('dashboard.get', sha1)
        bundle = json.loads(result_bundle['content'])

        host = [t for t in bundle['test_runs'] if t['test_id'] == 'art-microbenchmarks']
        if host:
            host = iter(host).next()
        else:
            return (None, None)
        json_attachments = [(a['pathname'], a['content']) for a in host['attachments'] if a['pathname'].endswith('json')]

        if not json_attachments:
            return (None, None)
        return (json_attachments[0][0], base64.b64decode(json_attachments[0][1]))


class ArtWATestResults(LavaTestSystem):
    def get_test_job_results(self, test_job_id):
        # extract postprocessing results only
        status = self.call_xmlrpc('scheduler.job_status', test_job_id)

        if not ('bundle_sha1' in status and status['bundle_sha1']):
            return []

        test_result_list = []

        sha1 = status['bundle_sha1']
        result_bundle = self.call_xmlrpc('dashboard.get', sha1)
        bundle = json.loads(result_bundle['content'])

        target = [t for t in bundle['test_runs'] if t['test_id'] == 'wa2-target']
        if target:
            target = iter(target).next()
        else:
            return test_result_list
        host = [t for t in bundle['test_runs'] if t['test_id'] == 'wa2-host-postprocessing']
        if host:
            host = iter(host).next()
        else:
            return test_result_list
        src = (s for s in host['software_context']['sources'] if 'test_params' in s).next()
        db_attachments = [a['content'] for a in host['attachments'] if a['pathname'].endswith('db')]

        # select iteration, workload, metric, value from results;
        test_result_dict = {}
        if db_attachments:
            import sqlite3

            db_file_name = "/tmp/%s.db" % test_job_id
            db_file = open(db_file_name, "w")
            db_file.write(base64.b64decode(db_attachments[0]))
            db_file.close()
            conn = sqlite3.connect(db_file_name)
            cursor = conn.cursor()
            for row in cursor.execute("select iteration, workload, metric, value from results"):
                if row[1] in test_result_dict.keys():
                    test_result = test_result_dict[row[1]]
                    test_result['subscore'].append({
                            'name': row[2],
                            'measurement': row[3]
                        })
                else:
                    test_result = {}
                    test_result['board'] = target['attributes']['target']
                    test_result['board_config'] = target['attributes']['target']
                    # benchmark iteration
                    test_result['benchmark_name'] = row[1]
                    test_result['subscore'] = [{
                            'name': row[2],
                            'measurement': row[3]
                        }]
                    test_result_dict[row[1]] = test_result
            os.unlink(db_file_name)
        return [value for key, value in test_result_dict.iteritems()]

    def get_result_data(self, test_job_id):
        status = self.call_xmlrpc('scheduler.job_status', test_job_id)

        if not ('bundle_sha1' in status and status['bundle_sha1']):
            return (None, None)

        sha1 = status['bundle_sha1']
        result_bundle = self.call_xmlrpc('dashboard.get', sha1)
        bundle = json.loads(result_bundle['content'])

        host = [t for t in bundle['test_runs'] if t['test_id'] == 'wa2-host-postprocessing']
        if host:
            host = iter(host).next()
        else:
            return (None, None)
        db_attachments = [(a['pathname'], a['content']) for a in host['attachments'] if a['pathname'].endswith('db')]

        if not db_attachments:
            return (None, None)
        return (db_attachments[0][0], base64.b64decode(db_attachments[0][1]))


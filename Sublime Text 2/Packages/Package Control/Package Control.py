# coding=utf-8
import sublime
import sublime_plugin
import os
import sys
import subprocess
import zipfile
import urllib
import urllib2
import json
from fnmatch import fnmatch
import re
import threading
import datetime
import time
import shutil
import _strptime
import tempfile

try:
    import ssl
    import httplib
    import socket

    class InvalidCertificateException(httplib.HTTPException, urllib2.URLError):
        def __init__(self, host, cert, reason):
            httplib.HTTPException.__init__(self)
            self.host = host
            self.cert = cert
            self.reason = reason

        def __str__(self):
            return ('Host %s returned an invalid certificate (%s) %s\n' %
                    (self.host, self.reason, self.cert))

    class CertValidatingHTTPSConnection(httplib.HTTPConnection):
        default_port = httplib.HTTPS_PORT

        def __init__(self, host, port=None, key_file=None, cert_file=None,
                                 ca_certs=None, strict=None, **kwargs):
            httplib.HTTPConnection.__init__(self, host, port, strict, **kwargs)
            self.key_file = key_file
            self.cert_file = cert_file
            self.ca_certs = ca_certs
            if self.ca_certs:
                self.cert_reqs = ssl.CERT_REQUIRED
            else:
                self.cert_reqs = ssl.CERT_NONE

        def _GetValidHostsForCert(self, cert):
            if 'subjectAltName' in cert:
                return [x[1] for x in cert['subjectAltName']
                             if x[0].lower() == 'dns']
            else:
                return [x[0][1] for x in cert['subject']
                                if x[0][0].lower() == 'commonname']

        def _ValidateCertificateHostname(self, cert, hostname):
            hosts = self._GetValidHostsForCert(cert)
            for host in hosts:
                host_re = host.replace('.', '\.').replace('*', '[^.]*')
                if re.search('^%s$' % (host_re,), hostname, re.I):
                    return True
            return False

        def connect(self):
            sock = socket.create_connection((self.host, self.port))
            self.sock = ssl.wrap_socket(sock, keyfile=self.key_file,
                                              certfile=self.cert_file,
                                              cert_reqs=self.cert_reqs,
                                              ca_certs=self.ca_certs)
            if self.cert_reqs & ssl.CERT_REQUIRED:
                cert = self.sock.getpeercert()
                hostname = self.host.split(':', 0)[0]
                if not self._ValidateCertificateHostname(cert, hostname):
                    raise InvalidCertificateException(hostname, cert,
                                                      'hostname mismatch')

    if hasattr(urllib2, 'HTTPSHandler'):
        class VerifiedHTTPSHandler(urllib2.HTTPSHandler):
            def __init__(self, **kwargs):
                urllib2.AbstractHTTPHandler.__init__(self)
                self._connection_args = kwargs

            def https_open(self, req):
                def http_class_wrapper(host, **kwargs):
                    full_kwargs = dict(self._connection_args)
                    full_kwargs.update(kwargs)
                    return CertValidatingHTTPSConnection(host, **full_kwargs)

                try:
                    return self.do_open(http_class_wrapper, req)
                except urllib2.URLError, e:
                    if type(e.reason) == ssl.SSLError and e.reason.args[0] == 1:
                        raise InvalidCertificateException(req.host, '',
                                                          e.reason.args[1])
                    raise

            https_request = urllib2.HTTPSHandler.do_request_

except (ImportError):
    pass


class ThreadProgress():
    def __init__(self, thread, message, success_message):
        self.thread = thread
        self.message = message
        self.success_message = success_message
        self.addend = 1
        self.size = 8
        sublime.set_timeout(lambda: self.run(0), 100)

    def run(self, i):
        if not self.thread.is_alive():
            if hasattr(self.thread, 'result') and not self.thread.result:
                sublime.status_message('')
                return
            sublime.status_message(self.success_message)
            return

        before = i % self.size
        after = (self.size - 1) - before
        sublime.status_message('%s [%s=%s]' % \
            (self.message, ' ' * before, ' ' * after))
        if not after:
            self.addend = -1
        if not before:
            self.addend = 1
        i += self.addend
        sublime.set_timeout(lambda: self.run(i), 100)


class ChannelProvider():
    def __init__(self, channel, package_manager):
        self.channel_info = None
        self.channel = channel
        self.package_manager = package_manager

    def match_url(self):
        return True

    def fetch_channel(self):
        if self.channel_info != None:
            return

        channel_json = self.package_manager.download_url(self.channel,
            'Error downloading channel.')
        if channel_json == False:
            self.channel_info = False
            return

        try:
            channel_info = json.loads(channel_json)
        except (ValueError):
            sublime.error_message(('%s: Error parsing JSON from ' +
                'channel %s.') % (__name__, self.channel))
            channel_info = False

        self.channel_info = channel_info

    def get_name_map(self):
        self.fetch_channel()
        if self.channel_info == False:
            return False
        return self.channel_info.get('package_name_map', {})

    def get_renamed_packages(self):
        self.fetch_channel()
        if self.channel_info == False:
            return False
        return self.channel_info.get('renamed_packages', {})

    def get_repositories(self):
        self.fetch_channel()
        if self.channel_info == False:
            return False
        return self.channel_info['repositories']

    def get_certs(self):
        self.fetch_channel()
        if self.channel_info == False:
            return False
        return self.channel_info.get('certs', {})

    def get_packages(self, repo):
        self.fetch_channel()
        if self.channel_info == False:
            return False
        if self.channel_info.get('packages', False) == False:
            return False
        if self.channel_info['packages'].get(repo, False) == False:
            return False
        output = {}
        for package in self.channel_info['packages'][repo]:
            copy = package.copy()

            platforms = copy['platforms'].keys()
            if sublime.platform() in platforms:
                copy['downloads'] = copy['platforms'][sublime.platform()]
            elif '*' in platforms:
                copy['downloads'] = copy['platforms']['*']
            else:
                continue
            del copy['platforms']

            copy['url'] = copy['homepage']
            del copy['homepage']

            output[copy['name']] = copy
        return output


_channel_providers = [ChannelProvider]


class PackageProvider():
    def __init__(self, repo, package_manager):
        self.repo_info = None
        self.repo = repo
        self.package_manager = package_manager

    def match_url(self):
        return True

    def fetch_repo(self):
        if self.repo_info != None:
            return

        repository_json = self.package_manager.download_url(self.repo,
            'Error downloading repository.')
        if repository_json == False:
            self.repo_info = False
            return

        try:
            self.repo_info = json.loads(repository_json)
        except (ValueError):
            sublime.error_message(('%s: Error parsing JSON from ' +
                'repository %s.') % (__name__, self.repo))
            self.repo_info = False

    def get_packages(self):
        self.fetch_repo()
        if self.repo_info == False:
            return False

        identifiers = [sublime.platform() + '-' + sublime.arch(),
            sublime.platform(), '*']
        output = {}
        for package in self.repo_info['packages']:
            for id in identifiers:
                if not id in package['platforms']:
                    continue

                downloads = []
                for download in package['platforms'][id]:
                    downloads.append(download)

                info = {
                    'name': package['name'],
                    'description': package.get('description'),
                    'url': package.get('homepage', self.repo),
                    'author': package.get('author'),
                    'last_modified': package.get('last_modified'),
                    'downloads': downloads
                }

                output[package['name']] = info
                break
        return output

    def get_renamed_packages(self):
        return self.repo_info.get('renamed_packages', {})


class GitHubPackageProvider():
    def __init__(self, repo, package_manager):
        self.repo_info = None
        self.repo = repo
        self.package_manager = package_manager

    def match_url(self):
        master = re.search('^https?://github.com/[^/]+/[^/]+/?$', self.repo)
        branch = re.search('^https?://github.com/[^/]+/[^/]+/tree/[^/]+/?$',
            self.repo)
        return master != None or branch != None

    def get_packages(self):
        branch = 'master'
        branch_match = re.search(
            '^https?://github.com/[^/]+/[^/]+/tree/([^/]+)/?$', self.repo)
        if branch_match != None:
            branch = branch_match.group(1)

        api_url = re.sub('^https?://github.com/([^/]+)/([^/]+)($|/.*$)',
            'https://api.github.com/repos/\\1/\\2', self.repo)

        repo_json = self.package_manager.download_url(api_url,
            'Error downloading repository.')
        if repo_json == False:
            return False

        try:
            repo_info = json.loads(repo_json)
        except (ValueError):
            sublime.error_message(('%s: Error parsing JSON from ' +
                'repository %s.') % (__name__, api_url))
            return False

        commit_api_url = api_url + '/commits?' + \
            urllib.urlencode({'sha': branch, 'per_page': 1})

        commit_json = self.package_manager.download_url(commit_api_url,
            'Error downloading repository.')
        if commit_json == False:
            return False

        try:
            commit_info = json.loads(commit_json)
        except (ValueError):
            sublime.error_message(('%s: Error parsing JSON from ' +
                'repository %s.') % (__name__, commit_api_url))
            return False

        download_url = 'https://nodeload.github.com/' + \
            repo_info['owner']['login'] + '/' + \
            repo_info['name'] + '/zipball/' + urllib.quote(branch)

        commit_date = commit_info[0]['commit']['committer']['date']
        timestamp = datetime.datetime.strptime(commit_date[0:19],
            '%Y-%m-%dT%H:%M:%S')
        utc_timestamp = timestamp.strftime(
            '%Y.%m.%d.%H.%M.%S')

        homepage = repo_info['homepage']
        if not homepage:
            homepage = repo_info['html_url']

        package = {
            'name': repo_info['name'],
            'description': repo_info['description'] if \
                repo_info['description'] else 'No description provided',
            'url': homepage,
            'author': repo_info['owner']['login'],
            'last_modified': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'downloads': [
                {
                    'version': utc_timestamp,
                    'url': download_url
                }
            ]
        }
        return {package['name']: package}

    def get_renamed_packages(self):
        return {}


class GitHubUserProvider():
    def __init__(self, repo, package_manager):
        self.repo_info = None
        self.repo = repo
        self.package_manager = package_manager

    def match_url(self):
        return re.search('^https?://github.com/[^/]+/?$', self.repo) != None

    def get_packages(self):
        user_match = re.search('^https?://github.com/([^/]+)/?$', self.repo)
        user = user_match.group(1)

        api_url = 'https://api.github.com/users/%s/repos?per_page=100' % user

        repo_json = self.package_manager.download_url(api_url,
            'Error downloading repository.')
        if repo_json == False:
            return False

        try:
            repo_info = json.loads(repo_json)
        except (ValueError):
            sublime.error_message(('%s: Error parsing JSON from ' +
                'repository %s.') % (__name__, api_url))
            return False

        packages = {}
        for package_info in repo_info:
            commit_api_url = ('https://api.github.com/repos/%s/%s/commits' + \
                '?sha=master&per_page=1') % (user, package_info['name'])

            commit_json = self.package_manager.download_url(commit_api_url,
                'Error downloading repository.')
            if commit_json == False:
                return False

            try:
                commit_info = json.loads(commit_json)
            except (ValueError):
                sublime.error_message(('%s: Error parsing JSON from ' +
                    'repository %s.') % (__name__, commit_api_url))
                return False

            commit_date = commit_info[0]['commit']['committer']['date']
            timestamp = datetime.datetime.strptime(commit_date[0:19],
                '%Y-%m-%dT%H:%M:%S')
            utc_timestamp = timestamp.strftime(
                '%Y.%m.%d.%H.%M.%S')

            homepage = package_info['homepage']
            if not homepage:
                homepage = package_info['html_url']

            package = {
                'name': package_info['name'],
                'description': repo_info['description'] if \
                    repo_info['description'] else 'No description provided',
                'url': homepage,
                'author': package_info['owner']['login'],
                'last_modified': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'downloads': [
                    {
                        'version': utc_timestamp,
                        'url': 'https://nodeload.github.com/' + \
                            package_info['owner']['login'] + '/' + \
                            package_info['name'] + '/zipball/master'
                    }
                ]
            }
            packages[package['name']] = package
        return packages

    def get_renamed_packages(self):
        return {}


class BitBucketPackageProvider():
    def __init__(self, repo, package_manager):
        self.repo_info = None
        self.repo = repo
        self.package_manager = package_manager

    def match_url(self):
        return re.search('^https?://bitbucket.org', self.repo) != None

    def get_packages(self):
        api_url = re.sub('^https?://bitbucket.org/',
            'https://api.bitbucket.org/1.0/repositories/', self.repo)
        api_url = api_url.rstrip('/')
        repo_json = self.package_manager.download_url(api_url,
            'Error downloading repository.')
        if repo_json == False:
            return False
        try:
            repo_info = json.loads(repo_json)
        except (ValueError):
            sublime.error_message(('%s: Error parsing JSON from ' +
                'repository %s.') % (__name__, api_url))
            return False

        changeset_url = api_url + '/changesets/default'
        changeset_json = self.package_manager.download_url(changeset_url,
            'Error downloading repository.')
        if changeset_json == False:
            return False
        try:
            last_commit = json.loads(changeset_json)
        except (ValueError):
            sublime.error_message(('%s: Error parsing JSON from ' +
                'repository %s.') % (__name__, changeset_url))
            return False
        commit_date = last_commit['timestamp']
        timestamp = datetime.datetime.strptime(commit_date[0:19],
            '%Y-%m-%d %H:%M:%S')
        utc_timestamp = timestamp.strftime(
            '%Y.%m.%d.%H.%M.%S')

        homepage = repo_info['website']
        if not homepage:
            homepage = self.repo
        package = {
            'name': repo_info['name'],
            'description': repo_info['description'] if \
                repo_info['description'] else 'No description provided',
            'url': homepage,
            'author': repo_info['owner'],
            'last_modified': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'downloads': [
                {
                    'version': utc_timestamp,
                    'url': self.repo + '/get/' + \
                        last_commit['node'] + '.zip'
                }
            ]
        }
        return {package['name']: package}

    def get_renamed_packages(self):
        return {}


_package_providers = [BitBucketPackageProvider, GitHubPackageProvider,
    GitHubUserProvider, PackageProvider]


class BinaryNotFoundError(Exception):
    pass


class NonCleanExitError(Exception):
    def __init__(self, returncode):
        self.returncode = returncode

    def __str__(self):
        return repr(self.returncode)


class Downloader():
    def check_certs(self, domain, timeout):
        cert_info = self.settings.get('certs', {}).get(
            domain)
        if not cert_info:
            print '%s: No CA certs available for %s.' % (__name__,
                domain)
            return False
        cert_path = os.path.join(sublime.packages_path(), 'Package Control',
            'certs', cert_info[0])
        ca_bundle_path = os.path.join(sublime.packages_path(),
            'Package Control', 'certs', 'ca-bundle.crt')
        if not os.path.exists(cert_path):
            cert_downloader = self.__class__(self.settings)
            cert_contents = cert_downloader.download(cert_info[1],
                'Error downloading CA certs for %s.' % (domain), timeout, 1)
            if not cert_contents:
                return False
            with open(cert_path, 'wb') as f:
                f.write(cert_contents)
            with open(ca_bundle_path, 'ab') as f:
                f.write("\n" + cert_contents)
        return ca_bundle_path


class CliDownloader(Downloader):
    def __init__(self, settings):
        self.settings = settings

    def find_binary(self, name):
        for dir in os.environ['PATH'].split(os.pathsep):
            path = os.path.join(dir, name)
            if os.path.exists(path):
                return path

        raise BinaryNotFoundError('The binary %s could not be located' % name)

    def execute(self, args):
        proc = subprocess.Popen(args, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        output = proc.stdout.read()
        returncode = proc.wait()
        if returncode != 0:
            error = NonCleanExitError(returncode)
            error.output = output
            raise error
        return output


class UrlLib2Downloader(Downloader):
    def __init__(self, settings):
        self.settings = settings

    def download(self, url, error_message, timeout, tries):
        http_proxy = self.settings.get('http_proxy')
        https_proxy = self.settings.get('https_proxy')
        if http_proxy or https_proxy:
            proxies = {}
            if http_proxy:
                proxies['http'] = http_proxy
                if not https_proxy:
                    proxies['https'] = http_proxy
            if https_proxy:
                proxies['https'] = https_proxy
            proxy_handler = urllib2.ProxyHandler(proxies)
        else:
            proxy_handler = urllib2.ProxyHandler()
        handlers = [proxy_handler]

        secure_url_match = re.match('^https://([^/]+)', url)
        if secure_url_match != None:
            secure_domain = secure_url_match.group(1)
            bundle_path = self.check_certs(secure_domain, timeout)
            if not bundle_path:
                return False
            handlers.append(VerifiedHTTPSHandler(ca_certs=bundle_path))
        urllib2.install_opener(urllib2.build_opener(*handlers))

        while tries > 0:
            tries -= 1
            try:
                request = urllib2.Request(url, headers={"User-Agent":
                    "Sublime Package Control"})
                http_file = urllib2.urlopen(request, timeout=timeout)
                return http_file.read()

            except (urllib2.HTTPError) as (e):
                # Bitbucket and Github ratelimit using 503 a decent amount
                if str(e.code) == '503':
                    print ('%s: Downloading %s was rate limited, ' +
                        'trying again') % (__name__, url)
                    continue
                print '%s: %s HTTP error %s downloading %s.' % (__name__,
                    error_message, str(e.code), url)

            except (urllib2.URLError) as (e):
                # Bitbucket and Github timeout a decent amount
                if str(e.reason) == 'The read operation timed out' or \
                        str(e.reason) == 'timed out':
                    print ('%s: Downloading %s timed out, trying ' +
                        'again') % (__name__, url)
                    continue
                print '%s: %s URL error %s downloading %s.' % (__name__,
                    error_message, str(e.reason), url)
            break
        return False


class WgetDownloader(CliDownloader):
    def __init__(self, settings):
        self.settings = settings
        self.wget = self.find_binary('wget')

    def clean_tmp_file(self):
        os.remove(self.tmp_file)

    def download(self, url, error_message, timeout, tries):
        if not self.wget:
            return False

        self.tmp_file = tempfile.NamedTemporaryFile().name
        command = [self.wget, '--connect-timeout=' + str(int(timeout)), '-o',
            self.tmp_file, '-O', '-', '-U', 'Sublime Package Control']

        secure_url_match = re.match('^https://([^/]+)', url)
        if secure_url_match != None:
            secure_domain = secure_url_match.group(1)
            bundle_path = self.check_certs(secure_domain, timeout)
            if not bundle_path:
                return False
            command.append(u'--ca-certificate=' + bundle_path)

        command.append(url)

        if self.settings.get('http_proxy'):
            os.putenv('http_proxy', self.settings.get('http_proxy'))
            if not self.settings.get('https_proxy'):
                os.putenv('https_proxy', self.settings.get('http_proxy'))
        if self.settings.get('https_proxy'):
            os.putenv('https_proxy', self.settings.get('https_proxy'))

        while tries > 0:
            tries -= 1
            try:
                result = self.execute(command)
                self.clean_tmp_file()
                return result
            except (NonCleanExitError) as (e):
                error_line = ''
                with open(self.tmp_file) as f:
                    for line in list(f):
                        if re.search('ERROR[: ]|failed: ', line):
                            error_line = line
                            break

                if e.returncode == 8:
                    regex = re.compile('^.*ERROR (\d+):.*', re.S)
                    if re.sub(regex, '\\1', error_line) == '503':
                        # GitHub and BitBucket seem to rate limit via 503
                        print ('%s: Downloading %s was rate limited' +
                            ', trying again') % (__name__, url)
                        continue
                    error_string = 'HTTP error ' + re.sub('^.*? ERROR ', '',
                        error_line)

                elif e.returncode == 4:
                    error_string = re.sub('^.*?failed: ', '', error_line)
                    # GitHub and BitBucket seem to time out a lot
                    if error_string.find('timed out') != -1:
                        print ('%s: Downloading %s timed out, ' +
                            'trying again') % (__name__, url)
                        continue

                else:
                    error_string = re.sub('^.*?(ERROR[: ]|failed: )', '\\1',
                        error_line)

                error_string = re.sub('\\.?\s*\n\s*$', '', error_string)
                print '%s: %s %s downloading %s.' % (__name__, error_message,
                    error_string, url)
            self.clean_tmp_file()
            break
        return False


class CurlDownloader(CliDownloader):
    def __init__(self, settings):
        self.settings = settings
        self.curl = self.find_binary('curl')

    def download(self, url, error_message, timeout, tries):
        if not self.curl:
            return False
        command = [self.curl, '-f', '--user-agent', 'Sublime Package Control',
            '--connect-timeout', str(int(timeout)), '-sS']

        secure_url_match = re.match('^https://([^/]+)', url)
        if secure_url_match != None:
            secure_domain = secure_url_match.group(1)
            bundle_path = self.check_certs(secure_domain, timeout)
            if not bundle_path:
                return False
            command.extend(['--cacert', bundle_path])

        command.append(url)

        if self.settings.get('http_proxy'):
            os.putenv('http_proxy', self.settings.get('http_proxy'))
            if not self.settings.get('https_proxy'):
                os.putenv('HTTPS_PROXY', self.settings.get('http_proxy'))
        if self.settings.get('https_proxy'):
            os.putenv('HTTPS_PROXY', self.settings.get('https_proxy'))

        while tries > 0:
            tries -= 1
            try:
                return self.execute(command)
            except (NonCleanExitError) as (e):
                if e.returncode == 22:
                    code = re.sub('^.*?(\d+)\s*$', '\\1', e.output)
                    if code == '503':
                        # GitHub and BitBucket seem to rate limit via 503
                        print ('%s: Downloading %s was rate limited' +
                            ', trying again') % (__name__, url)
                        continue
                    error_string = 'HTTP error ' + code
                elif e.returncode == 6:
                    error_string = 'URL error host not found'
                elif e.returncode == 28:
                    # GitHub and BitBucket seem to time out a lot
                    print ('%s: Downloading %s timed out, trying ' +
                        'again') % (__name__, url)
                    continue
                else:
                    error_string = e.output.rstrip()

                print '%s: %s %s downloading %s.' % (__name__, error_message,
                    error_string, url)
            break
        return False

_channel_repository_cache = {}


class RepositoryDownloader(threading.Thread):
    def __init__(self, package_manager, name_map, repo):
        self.package_manager = package_manager
        self.repo = repo
        self.packages = {}
        self.name_map = name_map
        threading.Thread.__init__(self)

    def run(self):
        for provider_class in _package_providers:
            provider = provider_class(self.repo, self.package_manager)
            if provider.match_url():
                break
        packages = provider.get_packages()
        if packages == False:
            self.packages = False
            return

        mapped_packages = {}
        for package in packages.keys():
            mapped_package = self.name_map.get(package, package)
            mapped_packages[mapped_package] = packages[package]
            mapped_packages[mapped_package]['name'] = mapped_package
        packages = mapped_packages

        self.packages = packages

        self.renamed_packages = provider.get_renamed_packages()


class VcsUpgrader():
    def __init__(self, vcs_binary, update_command, working_copy, cache_length):
        self.binary = vcs_binary
        self.update_command = update_command
        self.working_copy = working_copy
        self.cache_length = cache_length

    def execute(self, args, dir):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.Popen(args, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            startupinfo=startupinfo, cwd=dir)

        return proc.stdout.read().replace('\r\n', '\n').rstrip(' \n\r')

    def find_binary(self, name):
        if self.binary:
            return self.binary

        # Try the path first
        for dir in os.environ['PATH'].split(os.pathsep):
            path = os.path.join(dir, name)
            if os.path.exists(path):
                return path

        # This is left in for backwards compatibility and for windows
        # users who may have the binary, albeit in a common dir that may
        # not be part of the PATH
        if os.name == 'nt':
            dirs = ['C:\\Program Files\\Git\\bin',
                'C:\\Program Files (x86)\\Git\\bin',
                'C:\\Program Files\\TortoiseGit\\bin',
                'C:\\Program Files\\Mercurial',
                'C:\\Program Files (x86)\\Mercurial',
                'C:\\Program Files (x86)\\TortoiseHg',
                'C:\\Program Files\\TortoiseHg',
                'C:\\cygwin\\bin']
        else:
            dirs = ['/usr/local/git/bin']

        for dir in dirs:
            path = os.path.join(dir, name)
            if os.path.exists(path):
                return path

        return None


class GitUpgrader(VcsUpgrader):
    def retrieve_binary(self):
        name = 'git'
        if os.name == 'nt':
            name += '.exe'
        binary = self.find_binary(name)
        if binary and os.path.isdir(binary):
            full_path = os.path.join(binary, name)
            if os.path.exists(full_path):
                binary = full_path
        if not binary:
            sublime.error_message(('%s: Unable to find %s. ' +
                'Please set the git_binary setting by accessing the ' +
                'Preferences > Package Settings > %s > ' +
                u'Settings – User menu entry. The Settings – Default entry ' +
                'can be used for reference, but changes to that will be ' +
                'overwritten upon next upgrade.') % (__name__, name, __name__))
            return False

        if os.name == 'nt':
            tortoise_plink = self.find_binary('TortoisePlink.exe')
            if tortoise_plink:
                os.environ.setdefault('GIT_SSH', tortoise_plink)
        return binary

    def run(self):
        binary = self.retrieve_binary()
        if not binary:
            return False
        args = [binary]
        args.extend(self.update_command)
        self.execute(args, self.working_copy)
        return True

    def incoming(self):
        cache_key = self.working_copy + '.incoming'
        working_copy_cache = _channel_repository_cache.get(cache_key)
        if working_copy_cache and working_copy_cache.get('time') > \
                time.time():
            return working_copy_cache.get('data')

        binary = self.retrieve_binary()
        if not binary:
            return False
        self.execute([binary, 'fetch'], self.working_copy)
        args = [binary, 'log']
        args.append('..' + '/'.join(self.update_command[-2:]))
        output = self.execute(args, self.working_copy)
        incoming = len(output) > 0

        _channel_repository_cache[cache_key] = {
            'time': time.time() + self.cache_length,
            'data': incoming
        }
        return incoming


class HgUpgrader(VcsUpgrader):
    def retrieve_binary(self):
        name = 'hg'
        if os.name == 'nt':
            name += '.exe'
        binary = self.find_binary(name)
        if binary and os.path.isdir(binary):
            full_path = os.path.join(binary, name)
            if os.path.exists(full_path):
                binary = full_path
        if not binary:
            sublime.error_message(('%s: Unable to find %s. ' +
                'Please set the hg_binary setting by accessing the ' +
                'Preferences > Package Settings > %s > ' +
                u'Settings – User menu entry. The Settings – Default entry ' +
                'can be used for reference, but changes to that will be ' +
                'overwritten upon next upgrade.') % (__name__, name, __name__))
            return False
        return binary

    def run(self):
        binary = self.retrieve_binary()
        if not binary:
            return False
        args = [binary]
        args.extend(self.update_command)
        self.execute(args, self.working_copy)
        return True

    def incoming(self):
        cache_key = self.working_copy + '.incoming'
        working_copy_cache = _channel_repository_cache.get(cache_key)
        if working_copy_cache and working_copy_cache.get('time') > \
                time.time():
            return working_copy_cache.get('data')

        binary = self.retrieve_binary()
        if not binary:
            return False
        args = [binary, 'in', '-q']
        args.append(self.update_command[-1])
        output = self.execute(args, self.working_copy)
        incoming = len(output) > 0

        _channel_repository_cache[cache_key] = {
            'time': time.time() + self.cache_length,
            'data': incoming
        }
        return incoming


class PackageManager():
    def __init__(self):
        # Here we manually copy the settings since sublime doesn't like
        # code accessing settings from threads
        self.settings = {}
        settings = sublime.load_settings(__name__ + '.sublime-settings')
        for setting in ['timeout', 'repositories', 'repository_channels',
                'package_name_map', 'dirs_to_ignore', 'files_to_ignore',
                'package_destination', 'cache_length', 'auto_upgrade',
                'files_to_ignore_binary', 'files_to_keep', 'dirs_to_keep',
                'git_binary', 'git_update_command', 'hg_binary',
                'hg_update_command', 'http_proxy', 'https_proxy',
                'auto_upgrade_ignore', 'auto_upgrade_frequency',
                'submit_usage', 'submit_url', 'renamed_packages',
                'files_to_include', 'files_to_include_binary', 'certs',
                'ignore_vcs_packages']:
            if settings.get(setting) == None:
                continue
            self.settings[setting] = settings.get(setting)
        self.settings['platform'] = sublime.platform()
        self.settings['version'] = sublime.version()

    def compare_versions(self, version1, version2):
        def normalize(v):
            # We prepend 0 to all date-based version numbers so that developers
            # may switch to explicit versioning from GitHub/BitBucket
            # versioning based on commit dates
            if re.match('\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}', v):
                v = '0.' + v
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
        return cmp(normalize(version1), normalize(version2))

    def download_url(self, url, error_message):
        has_ssl = 'ssl' in sys.modules and hasattr(urllib2, 'HTTPSHandler')
        is_ssl = re.search('^https://', url) != None

        if (is_ssl and has_ssl) or not is_ssl:
            downloader = UrlLib2Downloader(self.settings)
        else:
            for downloader_class in [CurlDownloader, WgetDownloader]:
                try:
                    downloader = downloader_class(self.settings)
                    break
                except (BinaryNotFoundError):
                    pass

        if not downloader:
            sublime.error_message(('%s: Unable to download %s due to no ' +
                'ssl module available and no capable program found. Please ' +
                'install curl or wget.') % (__name__, url))
            return False

        timeout = self.settings.get('timeout', 3)
        return downloader.download(url.replace(' ', '%20'), error_message,
            timeout, 3)

    def get_metadata(self, package):
        metadata_filename = os.path.join(self.get_package_dir(package),
            'package-metadata.json')
        if os.path.exists(metadata_filename):
            with open(metadata_filename) as f:
                try:
                    return json.load(f)
                except (ValueError):
                    return {}
        return {}

    def list_repositories(self):
        repositories = self.settings.get('repositories')
        repository_channels = self.settings.get('repository_channels')
        for channel in repository_channels:
            channel_repositories = None

            cache_key = channel + '.repositories'
            repositories_cache = _channel_repository_cache.get(cache_key)
            if repositories_cache and repositories_cache.get('time') > \
                    time.time():
                channel_repositories = repositories_cache.get('data')

            name_map_cache_key = channel + '.package_name_map'
            name_map_cache = _channel_repository_cache.get(
                name_map_cache_key)
            if name_map_cache and name_map_cache.get('time') > \
                    time.time():
                name_map = name_map_cache.get('data')
                name_map.update(self.settings.get('package_name_map', {}))
                self.settings['package_name_map'] = name_map

            renamed_cache_key = channel + '.renamed_packages'
            renamed_cache = _channel_repository_cache.get(
                renamed_cache_key)
            if renamed_cache and renamed_cache.get('time') > \
                    time.time():
                renamed_packages = renamed_cache.get('data')
                renamed_packages.update(self.settings.get('renamed_packages',
                    {}))
                self.settings['renamed_packages'] = renamed_packages

            certs_cache_key = channel + '.certs'
            certs_cache = _channel_repository_cache.get(certs_cache_key)
            if certs_cache and certs_cache.get('time') > time.time():
                certs = self.settings.get('certs', {})
                certs.update(certs_cache.get('data'))
                self.settings['certs'] = certs

            if channel_repositories == None or \
                    self.settings.get('package_name_map') == None or \
                    self.settings.get('renamed_packages') == None:
                for provider_class in _channel_providers:
                    provider = provider_class(channel, self)
                    if provider.match_url():
                        break

                channel_repositories = provider.get_repositories()

                if channel_repositories == False:
                    continue
                _channel_repository_cache[cache_key] = {
                    'time': time.time() + self.settings.get('cache_length',
                        300),
                    'data': channel_repositories
                }

                for repo in channel_repositories:
                    if provider.get_packages(repo) == False:
                        continue
                    packages_cache_key = repo + '.packages'
                    _channel_repository_cache[packages_cache_key] = {
                        'time': time.time() + self.settings.get('cache_length',
                            300),
                        'data': provider.get_packages(repo)
                    }

                # Have the local name map override the one from the channel
                name_map = provider.get_name_map()
                name_map.update(self.settings.get('package_name_map', {}))
                self.settings['package_name_map'] = name_map
                _channel_repository_cache[name_map_cache_key] = {
                    'time': time.time() + self.settings.get('cache_length',
                        300),
                    'data': name_map
                }

                renamed_packages = provider.get_renamed_packages()
                _channel_repository_cache[renamed_cache_key] = {
                    'time': time.time() + self.settings.get('cache_length',
                        300),
                    'data': renamed_packages
                }
                if renamed_packages:
                    self.settings['renamed_packages'] = self.settings.get(
                        'renamed_packages', {})
                    self.settings['renamed_packages'].update(renamed_packages)

                certs = provider.get_certs()
                _channel_repository_cache[certs_cache_key] = {
                    'time': time.time() + self.settings.get('cache_length',
                        300),
                    'data': certs
                }
                if certs:
                    self.settings['certs'] = self.settings.get('certs', {})
                    self.settings['certs'].update(certs)

            repositories.extend(channel_repositories)
        return repositories

    def list_available_packages(self):
        repositories = self.list_repositories()
        packages = {}
        downloaders = []
        grouped_downloaders = {}

        # Repositories are run in reverse order so that the ones first
        # on the list will overwrite those last on the list
        for repo in repositories[::-1]:
            repository_packages = None

            cache_key = repo + '.packages'
            packages_cache = _channel_repository_cache.get(cache_key)
            if packages_cache and packages_cache.get('time') > \
                    time.time():
                repository_packages = packages_cache.get('data')
                packages.update(repository_packages)

            if repository_packages == None:
                downloader = RepositoryDownloader(self,
                    self.settings.get('package_name_map', {}), repo)
                domain = re.sub('^https?://[^/]*?(\w+\.\w+)($|/.*$)', '\\1',
                    repo)
                if not grouped_downloaders.get(domain):
                    grouped_downloaders[domain] = []
                grouped_downloaders[domain].append(downloader)

        def schedule(downloader, delay):
            downloader.has_started = False

            def inner():
                downloader.start()
                downloader.has_started = True
            sublime.set_timeout(inner, delay)

        for domain_downloaders in grouped_downloaders.values():
            for i in range(len(domain_downloaders)):
                downloader = domain_downloaders[i]
                downloaders.append(downloader)
                schedule(downloader, i * 150)

        complete = []

        while downloaders:
            downloader = downloaders.pop()
            if downloader.has_started:
                downloader.join()
                complete.append(downloader)
            else:
                downloaders.insert(0, downloader)

        for downloader in complete:
            repository_packages = downloader.packages
            if repository_packages == False:
                continue
            cache_key = downloader.repo + '.packages'
            _channel_repository_cache[cache_key] = {
                'time': time.time() + self.settings.get('cache_length', 300),
                'data': repository_packages
            }
            packages.update(repository_packages)

            renamed_packages = downloader.renamed_packages
            if renamed_packages == False:
                continue
            renamed_cache_key = downloader.repo + '.renamed_packages'
            _channel_repository_cache[renamed_cache_key] = {
                'time': time.time() + self.settings.get('cache_length', 300),
                'data': renamed_packages
            }
            if renamed_packages:
                self.settings['renamed_packages'] = self.settings.get(
                    'renamed_packages', {})
                self.settings['renamed_packages'].update(renamed_packages)

        return packages

    def list_packages(self):
        package_names = os.listdir(sublime.packages_path())
        package_names = [path for path in package_names if
            os.path.isdir(os.path.join(sublime.packages_path(), path))]
        # Ignore things to be deleted
        ignored_packages = []
        for package in package_names:
            cleanup_file = os.path.join(sublime.packages_path(), package,
                'package-control.cleanup')
            if os.path.exists(cleanup_file):
                ignored_packages.append(package)
        packages = list(set(package_names) - set(ignored_packages) -
            set(self.list_default_packages()))
        packages = sorted(packages, key=lambda s: s.lower())
        return packages

    def list_all_packages(self):
        packages = os.listdir(sublime.packages_path())
        packages = sorted(packages, key=lambda s: s.lower())
        return packages

    def list_default_packages(self):
        files = os.listdir(os.path.join(os.path.dirname(
            sublime.packages_path()), 'Pristine Packages'))
        files = list(set(files) - set(os.listdir(
            sublime.installed_packages_path())))
        packages = [file.replace('.sublime-package', '') for file in files]
        packages = sorted(packages, key=lambda s: s.lower())
        return packages

    def get_package_dir(self, package):
        return os.path.join(sublime.packages_path(), package)

    def get_mapped_name(self, package):
        return self.settings.get('package_name_map', {}).get(package, package)

    def create_package(self, package_name, package_destination,
            binary_package=False):
        package_dir = self.get_package_dir(package_name) + '/'

        if not os.path.exists(package_dir):
            sublime.error_message(('%s: The folder for the package name ' +
                'specified, %s, does not exist in %s') %
                (__name__, package_name, sublime.packages_path()))
            return False

        package_filename = package_name + '.sublime-package'
        package_path = os.path.join(package_destination,
            package_filename)

        if not os.path.exists(sublime.installed_packages_path()):
            os.mkdir(sublime.installed_packages_path())

        if os.path.exists(package_path):
            os.remove(package_path)

        try:
            package_file = zipfile.ZipFile(package_path, "w",
                compression=zipfile.ZIP_DEFLATED)
        except (OSError, IOError) as (exception):
            sublime.error_message(('%s: An error occurred creating the ' +
                'package file %s in %s. %s') % (__name__, package_filename,
                package_destination, str(exception)))
            return False

        dirs_to_ignore = self.settings.get('dirs_to_ignore', [])
        if not binary_package:
            files_to_ignore = self.settings.get('files_to_ignore', [])
            files_to_include = self.settings.get('files_to_include', [])
        else:
            files_to_ignore = self.settings.get('files_to_ignore_binary', [])
            files_to_include = self.settings.get('files_to_include_binary', [])

        package_dir_regex = re.compile('^' + re.escape(package_dir))
        for root, dirs, files in os.walk(package_dir):
            [dirs.remove(dir) for dir in dirs if dir in dirs_to_ignore]
            paths = dirs
            paths.extend(files)
            for path in paths:
                full_path = os.path.join(root, path)
                relative_path = re.sub(package_dir_regex, '', full_path)

                ignore_matches = [fnmatch(relative_path, p) for p in files_to_ignore]
                include_matches = [fnmatch(relative_path, p) for p in files_to_include]
                if any(ignore_matches) and not any(include_matches):
                    continue

                if os.path.isdir(full_path):
                    continue
                package_file.write(full_path, relative_path)

        package_file.close()

        return True

    def install_package(self, package_name):
        packages = self.list_available_packages()

        if package_name not in packages.keys():
            sublime.error_message(('%s: The package specified, %s, is ' +
                'not available.') % (__name__, package_name))
            return False

        download = packages[package_name]['downloads'][0]
        url = download['url']

        package_filename = package_name + \
            '.sublime-package'
        package_path = os.path.join(sublime.installed_packages_path(),
            package_filename)
        pristine_package_path = os.path.join(os.path.dirname(
            sublime.packages_path()), 'Pristine Packages', package_filename)

        package_dir = self.get_package_dir(package_name)

        package_metadata_file = os.path.join(package_dir,
            'package-metadata.json')

        if os.path.exists(os.path.join(package_dir, '.git')):
            if self.settings.get('ignore_vcs_packages'):
                sublime.error_message(('%s: Skipping git package %s since ' +
                    'the setting ignore_vcs_packages is set to true') %
                    (__name__, package_name))
                return False
            return GitUpgrader(self.settings['git_binary'],
                self.settings['git_update_command'], package_dir,
                self.settings['cache_length']).run()
        elif os.path.exists(os.path.join(package_dir, '.hg')):
            if self.settings.get('ignore_vcs_packages'):
                sublime.error_message(('%s: Skipping hg package %s since ' +
                    'the setting ignore_vcs_packages is set to true') %
                    (__name__, package_name))
                return False
            return HgUpgrader(self.settings['hg_binary'],
                self.settings['hg_update_command'], package_dir,
                self.settings['cache_length']).run()

        is_upgrade = os.path.exists(package_metadata_file)
        old_version = None
        if is_upgrade:
            old_version = self.get_metadata(package_name).get('version')

        package_bytes = self.download_url(url, 'Error downloading package.')
        if package_bytes == False:
            return False
        with open(package_path, "wb") as package_file:
            package_file.write(package_bytes)

        if not os.path.exists(package_dir):
            os.mkdir(package_dir)

        # We create a backup copy incase something was edited
        else:
            try:
                backup_dir = os.path.join(os.path.dirname(
                    sublime.packages_path()), 'Backup',
                    datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                package_backup_dir = os.path.join(backup_dir, package_name)
                shutil.copytree(package_dir, package_backup_dir)
            except (OSError, IOError) as (exception):
                sublime.error_message(('%s: An error occurred while trying ' +
                    'to backup the package directory for %s. %s') %
                    (__name__, package_name, str(exception)))
                shutil.rmtree(package_backup_dir)
                return False

        try:
            package_zip = zipfile.ZipFile(package_path, 'r')
        except (zipfile.BadZipfile):
            sublime.error_message(('%s: An error occurred while ' +
                'trying to unzip the package file for %s. Please try ' +
                'installing the package again.') % (__name__, package_name))
            return False

        root_level_paths = []
        last_path = None
        for path in package_zip.namelist():
            last_path = path
            if path.find('/') in [len(path) - 1, -1]:
                root_level_paths.append(path)
            if path[0] == '/' or path.find('../') != -1 or path.find('..\\') != -1:
                sublime.error_message(('%s: The package specified, %s, ' +
                    'contains files outside of the package dir and cannot ' +
                    'be safely installed.') % (__name__, package_name))
                return False

        if last_path and len(root_level_paths) == 0:
            root_level_paths.append(last_path[0:last_path.find('/') + 1])

        os.chdir(package_dir)

        # Here we don’t use .extractall() since it was having issues on OS X
        skip_root_dir = len(root_level_paths) == 1 and \
            root_level_paths[0].endswith('/')
        extracted_paths = []
        for path in package_zip.namelist():
            dest = path
            try:
                if not isinstance(dest, unicode):
                    dest = unicode(dest, 'utf-8', 'strict')
            except (UnicodeDecodeError):
                dest = unicode(dest, 'cp1252', 'replace')

            if os.name == 'nt':
                regex = ':|\*|\?|"|<|>|\|'
                if re.search(regex, dest) != None:
                    print ('%s: Skipping file from package named %s due to ' +
                        'an invalid filename') % (__name__, path)
                    continue

            # If there was only a single directory in the package, we remove
            # that folder name from the paths as we extract entries
            if skip_root_dir:
                dest = dest[len(root_level_paths[0]):]

            if os.name == 'nt':
                dest = dest.replace('/', '\\')
            else:
                dest = dest.replace('\\', '/')

            dest = os.path.join(package_dir, dest)

            def add_extracted_dirs(dir):
                while dir not in extracted_paths:
                    extracted_paths.append(dir)
                    dir = os.path.dirname(dir)
                    if dir == package_dir:
                        break

            if path.endswith('/'):
                if not os.path.exists(dest):
                    os.makedirs(dest)
                add_extracted_dirs(dest)
            else:
                dest_dir = os.path.dirname(dest)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                add_extracted_dirs(dest_dir)
                extracted_paths.append(dest)
                try:
                    open(dest, 'wb').write(package_zip.read(path))
                except (IOError, UnicodeDecodeError):
                    print ('%s: Skipping file from package named %s due to ' +
                        'an invalid filename') % (__name__, path)
        package_zip.close()

        # Here we clean out any files that were not just overwritten
        try:
            for root, dirs, files in os.walk(package_dir, topdown=False):
                paths = [os.path.join(root, f) for f in files]
                paths.extend([os.path.join(root, d) for d in dirs])

                for path in paths:
                    if path in extracted_paths:
                        continue
                    if os.path.isdir(path):
                        os.rmdir(path)
                    else:
                        os.remove(path)

        except (OSError, IOError) as (e):
            sublime.error_message(('%s: An error occurred while trying to ' +
                'remove old files from the %s directory. %s') %
                (__name__, package_name, str(e)))
            return False

        self.print_messages(package_name, package_dir, is_upgrade, old_version)

        with open(package_metadata_file, 'w') as f:
            metadata = {
                "version": packages[package_name]['downloads'][0]['version'],
                "url": packages[package_name]['url'],
                "description": packages[package_name]['description']
            }
            json.dump(metadata, f)

        # Submit install and upgrade info
        if is_upgrade:
            params = {
                'package': package_name,
                'operation': 'upgrade',
                'version': packages[package_name]['downloads'][0]['version'],
                'old_version': old_version
            }
        else:
            params = {
                'package': package_name,
                'operation': 'install',
                'version': packages[package_name]['downloads'][0]['version']
            }
        self.record_usage(params)

        # Record the install in the settings file so that you can move
        # settings across computers and have the same packages installed
        def save_package():
            settings = sublime.load_settings(__name__ + '.sublime-settings')
            installed_packages = settings.get('installed_packages', [])
            if not installed_packages:
                installed_packages = []
            installed_packages.append(package_name)
            installed_packages = list(set(installed_packages))
            installed_packages = sorted(installed_packages,
                key=lambda s: s.lower())
            settings.set('installed_packages', installed_packages)
            sublime.save_settings(__name__ + '.sublime-settings')
        sublime.set_timeout(save_package, 1)

        # Here we delete the package file from the installed packages directory
        # since we don't want to accidentally overwrite user changes
        os.remove(package_path)
        # We have to remove the pristine package too or else Sublime Text 2
        # will silently delete the package
        if os.path.exists(pristine_package_path):
            os.remove(pristine_package_path)

        os.chdir(sublime.packages_path())
        return True

    def print_messages(self, package, package_dir, is_upgrade, old_version):
        messages_file = os.path.join(package_dir, 'messages.json')
        if not os.path.exists(messages_file):
            return

        messages_fp = open(messages_file, 'r')
        message_info = json.load(messages_fp)
        messages_fp.close()

        output = ''
        if not is_upgrade and message_info.get('install'):
            install_messages = os.path.join(package_dir,
                message_info.get('install'))
            message = '\n\n%s:\n%s\n\n  ' % (package,
                        ('-' * len(package)))
            with open(install_messages, 'r') as f:
                message += f.read().replace('\n', '\n  ')
            output += message + '\n'

        elif is_upgrade and old_version:
            upgrade_messages = list(set(message_info.keys()) -
                set(['install']))
            upgrade_messages = sorted(upgrade_messages,
                cmp=self.compare_versions, reverse=True)
            for version in upgrade_messages:
                if self.compare_versions(old_version, version) >= 0:
                    break
                if not output:
                    message = '\n\n%s:\n%s\n' % (package,
                        ('-' * len(package)))
                    output += message
                upgrade_messages = os.path.join(package_dir,
                    message_info.get(version))
                message = '\n  '
                with open(upgrade_messages, 'r') as f:
                    message += f.read().replace('\n', '\n  ')
                output += message + '\n'

        if not output:
            return

        def print_to_panel():
            window = sublime.active_window()

            views = window.views()
            view = None
            for _view in views:
                if _view.name() == 'Package Control Messages':
                    view = _view
                    break

            if not view:
                view = window.new_file()
                view.set_name('Package Control Messages')
                view.set_scratch(True)

            def write(string):
                edit = view.begin_edit()
                view.insert(edit, view.size(), string)
                view.end_edit(edit)

            if not view.size():
                view.settings().set("word_wrap", True)
                write('Package Control Messages\n' +
                    '========================')

            write(output)
        sublime.set_timeout(print_to_panel, 1)

    def remove_package(self, package_name):
        installed_packages = self.list_packages()

        if package_name not in installed_packages:
            sublime.error_message(('%s: The package specified, %s, is not ' +
                'installed.') % (__name__, package_name))
            return False

        os.chdir(sublime.packages_path())

        # Give Sublime Text some time to ignore the package
        time.sleep(1)

        package_filename = package_name + '.sublime-package'
        package_path = os.path.join(sublime.installed_packages_path(),
            package_filename)
        installed_package_path = os.path.join(os.path.dirname(
            sublime.packages_path()), 'Installed Packages', package_filename)
        pristine_package_path = os.path.join(os.path.dirname(
            sublime.packages_path()), 'Pristine Packages', package_filename)
        package_dir = self.get_package_dir(package_name)

        version = self.get_metadata(package_name).get('version')

        try:
            if os.path.exists(package_path):
                os.remove(package_path)
        except (OSError, IOError) as (exception):
            sublime.error_message(('%s: An error occurred while trying to ' +
                'remove the package file for %s. %s') % (__name__,
                package_name, str(exception)))
            return False

        try:
            if os.path.exists(installed_package_path):
                os.remove(installed_package_path)
        except (OSError, IOError) as (exception):
            sublime.error_message(('%s: An error occurred while trying to ' +
                'remove the installed package file for %s. %s') % (__name__,
                package_name, str(exception)))
            return False

        try:
            if os.path.exists(pristine_package_path):
                os.remove(pristine_package_path)
        except (OSError, IOError) as (exception):
            sublime.error_message(('%s: An error occurred while trying to ' +
                'remove the pristine package file for %s. %s') % (__name__,
                package_name, str(exception)))
            return False

        # We don't delete the actual package dir immediately due to a bug
        # in sublime_plugin.py
        can_delete_dir = True
        for path in os.listdir(package_dir):
            try:
                full_path = os.path.join(package_dir, path)
                if not os.path.isdir(full_path):
                    os.remove(full_path)
                else:
                    shutil.rmtree(full_path)
            except (OSError, IOError) as (exception):
                # If there is an error deleting now, we will mark it for
                # cleanup the next time Sublime Text starts
                open(os.path.join(package_dir, 'package-control.cleanup'),
                    'w').close()
                can_delete_dir = False

        params = {
            'package': package_name,
            'operation': 'remove',
            'version': version
        }
        self.record_usage(params)

        # Remove the package from the installed packages list
        def clear_package():
            settings = sublime.load_settings('%s.sublime-settings' % __name__)
            installed_packages = settings.get('installed_packages', [])
            if not installed_packages:
                installed_packages = []
            installed_packages.remove(package_name)
            settings.set('installed_packages', installed_packages)
            sublime.save_settings('%s.sublime-settings' % __name__)
        sublime.set_timeout(clear_package, 1)

        if can_delete_dir:
            os.rmdir(package_dir)

        return True

    def record_usage(self, params):
        if not self.settings.get('submit_usage'):
            return
        params['package_control_version'] = \
            self.get_metadata('Package Control').get('version')
        params['sublime_platform'] = self.settings.get('platform')
        params['sublime_version'] = self.settings.get('version')
        url = self.settings.get('submit_url') + '?' + urllib.urlencode(params)

        result = self.download_url(url, 'Error submitting usage information.')
        if result == False:
            return

        try:
            result = json.loads(result)
            if result['result'] != 'success':
                raise ValueError()
        except (ValueError):
            print '%s: Error submitting usage information for %s' % (__name__,
                params['package'])


class PackageCreator():
    def show_panel(self):
        self.manager = PackageManager()
        self.packages = self.manager.list_packages()
        if not self.packages:
            sublime.error_message(('%s: There are no packages available to ' +
                'be packaged.') % (__name__))
            return
        self.window.show_quick_panel(self.packages, self.on_done)

    def get_package_destination(self):
        destination = self.manager.settings.get('package_destination')

        # We check destination via an if statement instead of using
        # the dict.get() method since the key may be set, but to a blank value
        if not destination:
            destination = os.path.join(os.path.expanduser('~'), 'Desktop')

        return destination


class CreatePackageCommand(sublime_plugin.WindowCommand, PackageCreator):
    def run(self):
        self.show_panel()

    def on_done(self, picked):
        if picked == -1:
            return
        package_name = self.packages[picked]
        package_destination = self.get_package_destination()

        if self.manager.create_package(package_name, package_destination):
            self.window.run_command('open_dir', {"dir":
                package_destination, "file": package_name +
                '.sublime-package'})


class CreateBinaryPackageCommand(sublime_plugin.WindowCommand, PackageCreator):
    def run(self):
        self.show_panel()

    def on_done(self, picked):
        if picked == -1:
            return
        package_name = self.packages[picked]
        package_destination = self.get_package_destination()

        if self.manager.create_package(package_name, package_destination,
                binary_package=True):
            self.window.run_command('open_dir', {"dir":
                package_destination, "file": package_name +
                '.sublime-package'})


class PackageInstaller():
    def __init__(self):
        self.manager = PackageManager()

    def make_package_list(self, ignore_actions=[], override_action=None,
            ignore_packages=[]):
        packages = self.manager.list_available_packages()
        installed_packages = self.manager.list_packages()

        package_list = []
        for package in sorted(packages.iterkeys(), key=lambda s: s.lower()):
            if ignore_packages and package in ignore_packages:
                continue
            package_entry = [package]
            info = packages[package]
            download = info['downloads'][0]

            if package in installed_packages:
                installed = True
                metadata = self.manager.get_metadata(package)
                if metadata.get('version'):
                    installed_version = metadata['version']
                else:
                    installed_version = None
            else:
                installed = False

            installed_version_name = 'v' + installed_version if \
                installed and installed_version else 'unknown version'
            new_version = 'v' + download['version']

            vcs = None
            package_dir = self.manager.get_package_dir(package)
            settings = self.manager.settings

            if override_action:
                action = override_action
                extra = ''

            else:
                if os.path.exists(os.path.join(sublime.packages_path(),
                        package, '.git')):
                    if settings.get('ignore_vcs_packages'):
                        continue
                    vcs = 'git'
                    incoming = GitUpgrader(settings.get('git_binary'),
                        settings.get('git_update_command'), package_dir,
                        settings.get('cache_length')).incoming()
                elif os.path.exists(os.path.join(sublime.packages_path(),
                        package, '.hg')):
                    if settings.get('ignore_vcs_packages'):
                        continue
                    vcs = 'hg'
                    incoming = HgUpgrader(settings.get('hg_binary'),
                        settings.get('hg_update_command'), package_dir,
                        settings.get('cache_length')).incoming()

                if installed:
                    if not installed_version:
                        if vcs:
                            if incoming:
                                action = 'pull'
                                extra = ' with ' + vcs
                            else:
                                action = 'none'
                                extra = ''
                        else:
                            action = 'overwrite'
                            extra = ' %s with %s' % (installed_version_name,
                                new_version)
                    else:
                        res = self.manager.compare_versions(
                            installed_version, download['version'])
                        if res < 0:
                            action = 'upgrade'
                            extra = ' to %s from %s' % (new_version,
                                installed_version_name)
                        elif res > 0:
                            action = 'downgrade'
                            extra = ' to %s from %s' % (new_version,
                                installed_version_name)
                        else:
                            action = 'reinstall'
                            extra = ' %s' % new_version
                else:
                    action = 'install'
                    extra = ' %s' % new_version
                extra += ';'

                if action in ignore_actions:
                    continue

            description = info.get('description')
            if not description:
                description = 'No description provided'
            package_entry.append(description)
            package_entry.append(action + extra + ' ' +
                re.sub('^https?://', '', info['url']))
            package_list.append(package_entry)
        return package_list

    def on_done(self, picked):
        if picked == -1:
            return
        name = self.package_list[picked][0]
        thread = PackageInstallerThread(self.manager, name)
        thread.start()
        ThreadProgress(thread, 'Installing package %s' % name,
            'Package %s successfully %s' % (name, self.completion_type))


class PackageInstallerThread(threading.Thread):
    def __init__(self, manager, package):
        self.package = package
        self.manager = manager
        threading.Thread.__init__(self)

    def run(self):
        self.result = self.manager.install_package(self.package)


class InstallPackageCommand(sublime_plugin.WindowCommand):
    def run(self):
        thread = InstallPackageThread(self.window)
        thread.start()
        ThreadProgress(thread, 'Loading repositories', '')


class InstallPackageThread(threading.Thread, PackageInstaller):
    def __init__(self, window):
        self.window = window
        self.completion_type = 'installed'
        threading.Thread.__init__(self)
        PackageInstaller.__init__(self)

    def run(self):
        self.package_list = self.make_package_list(['upgrade', 'downgrade',
            'reinstall', 'pull', 'none'])

        def show_quick_panel():
            if not self.package_list:
                sublime.error_message(('%s: There are no packages ' +
                    'available for installation.') % __name__)
                return
            self.window.show_quick_panel(self.package_list, self.on_done)
        sublime.set_timeout(show_quick_panel, 10)


class DiscoverPackagesCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command('open_url',
            {'url': 'http://wbond.net/sublime_packages/community'})


class UpgradePackageCommand(sublime_plugin.WindowCommand):
    def run(self):
        thread = UpgradePackageThread(self.window)
        thread.start()
        ThreadProgress(thread, 'Loading repositories', '')


class UpgradePackageThread(threading.Thread, PackageInstaller):
    def __init__(self, window):
        self.window = window
        self.completion_type = 'upgraded'
        threading.Thread.__init__(self)
        PackageInstaller.__init__(self)

    def run(self):
        self.package_list = self.make_package_list(['install', 'reinstall',
            'none'])

        def show_quick_panel():
            if not self.package_list:
                sublime.error_message(('%s: There are no packages ' +
                    'ready for upgrade.') % __name__)
                return
            self.window.show_quick_panel(self.package_list, self.on_done)
        sublime.set_timeout(show_quick_panel, 10)

    def on_done(self, picked):
        if picked == -1:
            return
        name = self.package_list[picked][0]
        thread = PackageInstallerThread(self.manager, name)
        thread.start()
        ThreadProgress(thread, 'Upgrading package %s' % name,
            'Package %s successfully %s' % (name, self.completion_type))


class UpgradeAllPackagesCommand(sublime_plugin.WindowCommand):
    def run(self):
        thread = UpgradeAllPackagesThread(self.window)
        thread.start()
        ThreadProgress(thread, 'Loading repositories', '')


class UpgradeAllPackagesThread(threading.Thread, PackageInstaller):
    def __init__(self, window):
        self.window = window
        self.completion_type = 'upgraded'
        threading.Thread.__init__(self)
        PackageInstaller.__init__(self)

    def run(self):
        for info in self.make_package_list(['install', 'reinstall', 'none']):
            thread = PackageInstallerThread(self.manager, info[0])
            thread.start()
            ThreadProgress(thread, 'Upgrading package %s' % info[0],
                'Package %s successfully %s' % (info[0], self.completion_type))


class ExistingPackagesCommand():
    def __init__(self):
        self.manager = PackageManager()

    def make_package_list(self, action=''):
        packages = self.manager.list_packages()

        if action:
            action += ' '

        package_list = []
        for package in sorted(packages, key=lambda s: s.lower()):
            package_entry = [package]
            metadata = self.manager.get_metadata(package)
            package_dir = os.path.join(sublime.packages_path(), package)

            description = metadata.get('description')
            if not description:
                description = 'No description provided'
            package_entry.append(description)

            version = metadata.get('version')
            if not version and os.path.exists(os.path.join(package_dir,
                    '.git')):
                installed_version = 'git repository'
            elif not version and os.path.exists(os.path.join(package_dir,
                    '.hg')):
                installed_version = 'hg repository'
            else:
                installed_version = 'v' + version if version else \
                    'unknown version'

            url = metadata.get('url')
            if url:
                url = '; ' + re.sub('^https?://', '', url)
            else:
                url = ''

            package_entry.append(action + installed_version + url)
            package_list.append(package_entry)

        return package_list


class ListPackagesCommand(sublime_plugin.WindowCommand):
    def run(self):
        ListPackagesThread(self.window).start()


class ListPackagesThread(threading.Thread, ExistingPackagesCommand):
    def __init__(self, window):
        self.window = window
        threading.Thread.__init__(self)
        ExistingPackagesCommand.__init__(self)

    def run(self):
        self.package_list = self.make_package_list()

        def show_quick_panel():
            if not self.package_list:
                sublime.error_message(('%s: There are no packages ' +
                    'to list.') % __name__)
                return
            self.window.show_quick_panel(self.package_list, self.on_done)
        sublime.set_timeout(show_quick_panel, 10)

    def on_done(self, picked):
        if picked == -1:
            return
        package_name = self.package_list[picked][0]

        def open_dir():
            self.window.run_command('open_dir',
                {"dir": os.path.join(sublime.packages_path(), package_name)})
        sublime.set_timeout(open_dir, 10)


class RemovePackageCommand(sublime_plugin.WindowCommand,
        ExistingPackagesCommand):
    def __init__(self, window):
        self.window = window
        ExistingPackagesCommand.__init__(self)

    def run(self):
        self.package_list = self.make_package_list('remove')
        if not self.package_list:
            sublime.error_message(('%s: There are no packages ' +
                'that can be removed.') % __name__)
            return
        self.window.show_quick_panel(self.package_list, self.on_done)

    def on_done(self, picked):
        if picked == -1:
            return
        package = self.package_list[picked][0]
        settings = sublime.load_settings('Global.sublime-settings')
        ignored_packages = settings.get('ignored_packages')
        if not ignored_packages:
            ignored_packages = []
        if not package in ignored_packages:
            ignored_packages.append(package)
            settings.set('ignored_packages', ignored_packages)
            sublime.save_settings('Global.sublime-settings')

        ignored_packages.remove(package)
        thread = RemovePackageThread(self.manager, package,
            ignored_packages)
        thread.start()
        ThreadProgress(thread, 'Removing package %s' % package,
            'Package %s successfully removed' % package)


class RemovePackageThread(threading.Thread):
    def __init__(self, manager, package, ignored_packages):
        self.manager = manager
        self.package = package
        self.ignored_packages = ignored_packages
        threading.Thread.__init__(self)

    def run(self):
        self.result = self.manager.remove_package(self.package)

        def unignore_package():
            settings = sublime.load_settings('Global.sublime-settings')
            settings.set('ignored_packages', self.ignored_packages)
            sublime.save_settings('Global.sublime-settings')
        sublime.set_timeout(unignore_package, 10)


class AddRepositoryChannelCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel('Channel JSON URL', '',
            self.on_done, self.on_change, self.on_cancel)

    def on_done(self, input):
        settings = sublime.load_settings('%s.sublime-settings' % __name__)
        repository_channels = settings.get('repository_channels', [])
        if not repository_channels:
            repository_channels = []
        repository_channels.append(input)
        settings.set('repository_channels', repository_channels)
        sublime.save_settings('%s.sublime-settings' % __name__)
        sublime.status_message(('Channel %s successfully ' +
            'added') % input)

    def on_change(self, input):
        pass

    def on_cancel(self):
        pass


class AddRepositoryCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel('GitHub or BitBucket Web URL, or Custom' +
                ' JSON Repository URL', '', self.on_done,
            self.on_change, self.on_cancel)

    def on_done(self, input):
        settings = sublime.load_settings('%s.sublime-settings' % __name__)
        repositories = settings.get('repositories', [])
        if not repositories:
            repositories = []
        repositories.append(input)
        settings.set('repositories', repositories)
        sublime.save_settings('%s.sublime-settings' % __name__)
        sublime.status_message('Repository %s successfully added' % input)

    def on_change(self, input):
        pass

    def on_cancel(self):
        pass


class DisablePackageCommand(sublime_plugin.WindowCommand):
    def run(self):
        manager = PackageManager()
        packages = manager.list_all_packages()
        self.settings = sublime.load_settings('Global.sublime-settings')
        disabled_packages = self.settings.get('ignored_packages')
        if not disabled_packages:
            disabled_packages = []
        self.package_list = list(set(packages) - set(disabled_packages))
        self.package_list.sort()
        if not self.package_list:
            sublime.error_message(('%s: There are no enabled packages' +
                'to disable.') % __name__)
            return
        self.window.show_quick_panel(self.package_list, self.on_done)

    def on_done(self, picked):
        if picked == -1:
            return
        package = self.package_list[picked]
        ignored_packages = self.settings.get('ignored_packages')
        if not ignored_packages:
            ignored_packages = []
        ignored_packages.append(package)
        self.settings.set('ignored_packages', ignored_packages)
        sublime.save_settings('Global.sublime-settings')
        sublime.status_message(('Package %s successfully added to list of ' +
            'disabled packages - restarting Sublime Text may be required') %
            package)


class EnablePackageCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.settings = sublime.load_settings('Global.sublime-settings')
        self.disabled_packages = self.settings.get('ignored_packages')
        self.disabled_packages.sort()
        if not self.disabled_packages:
            sublime.error_message(('%s: There are no disabled packages ' +
                'to enable.') % __name__)
            return
        self.window.show_quick_panel(self.disabled_packages, self.on_done)

    def on_done(self, picked):
        if picked == -1:
            return
        package = self.disabled_packages[picked]
        ignored = self.settings.get('ignored_packages')
        self.settings.set('ignored_packages',
            list(set(ignored) - set([package])))
        sublime.save_settings('Global.sublime-settings')
        sublime.status_message(('Package %s successfully removed from list ' +
            'of disabled packages - restarting Sublime Text may be required') %
            package)


class PackageStartup():
    def load_settings(self):
        self.settings_file = '%s.sublime-settings' % __name__
        self.settings = sublime.load_settings(self.settings_file)
        self.installed_packages = self.settings.get('installed_packages', [])
        if not isinstance(self.installed_packages, list):
            self.installed_packages = []

    def save_packages(self, installed_packages):
        installed_packages = list(set(installed_packages))
        installed_packages = sorted(installed_packages,
            key=lambda s: s.lower())

        if installed_packages != self.installed_packages:
            self.settings.set('installed_packages', installed_packages)
            sublime.save_settings(self.settings_file)


class AutomaticUpgrader(threading.Thread, PackageStartup):
    def __init__(self, found_packages):
        self.installer = PackageInstaller()
        self.manager = self.installer.manager
        self.load_settings()

        self.auto_upgrade = self.settings.get('auto_upgrade')
        self.auto_upgrade_ignore = self.settings.get('auto_upgrade_ignore')

        self.next_run = int(time.time())
        self.last_run = self.settings.get('auto_upgrade_last_run')

        frequency = self.settings.get('auto_upgrade_frequency')
        if frequency:
            if self.last_run:
                self.next_run = int(self.last_run) + (frequency * 60 * 60)
            else:
                self.next_run = time.time()

        # Detect if a package is missing that should be installed
        self.missing_packages = list(set(self.installed_packages) -
            set(found_packages))

        if self.auto_upgrade and self.next_run <= time.time():
            self.settings.set('auto_upgrade_last_run', int(time.time()))
            sublime.save_settings(self.settings_file)

        threading.Thread.__init__(self)

    def run(self):
        self.install_missing()

        if self.next_run > time.time():
            self.print_skip()
            return

        self.rename_packages()
        self.upgrade_packages()

    def install_missing(self):
        if not self.missing_packages:
            return

        print '%s: Installing %s missing packages' % \
            (__name__, len(self.missing_packages))
        for package in self.missing_packages:
            self.installer.manager.install_package(package)
            print '%s: Installed missing package %s' % \
                (__name__, package)

    def print_skip(self):
        last_run = datetime.datetime.fromtimestamp(self.last_run)
        next_run = datetime.datetime.fromtimestamp(self.next_run)
        date_format = '%Y-%m-%d %H:%M:%S'
        print ('%s: Skipping automatic upgrade, last run at ' +
            '%s, next run at %s or after') % (__name__,
            last_run.strftime(date_format), next_run.strftime(date_format))

    def rename_packages(self):
        # Fetch the packages since that will pull in the renamed packages list
        self.manager.list_available_packages()
        renamed_packages = self.manager.settings.get('renamed_packages', {})
        if not renamed_packages:
            renamed_packages = {}

        installed_pkgs = self.installed_packages

        # Rename directories for packages that have changed names
        for package_name in renamed_packages:
            package_dir = os.path.join(sublime.packages_path(), package_name)
            metadata_path = os.path.join(package_dir, 'package-metadata.json')
            if not os.path.exists(metadata_path):
                continue
            new_package_name = renamed_packages[package_name]
            new_package_dir = os.path.join(sublime.packages_path(),
                new_package_name)
            if not os.path.exists(new_package_dir):
                os.rename(package_dir, new_package_dir)
                installed_pkgs.append(new_package_name)
                print '%s: Renamed %s to %s' % (__name__, package_name,
                    new_package_name)
            else:
                self.installer.manager.remove_package(package_name)
                print ('%s: Removed %s since package with new name (%s) ' +
                    'already exists') % (__name__, package_name,
                    new_package_name)
            try:
                installed_pkgs.remove(package_name)
            except (ValueError):
                pass

        sublime.set_timeout(lambda: self.save_packages(installed_pkgs), 10)

    def upgrade_packages(self):
        if not self.auto_upgrade:
            return

        packages = self.installer.make_package_list(['install',
            'reinstall', 'downgrade', 'overwrite', 'none'],
            ignore_packages=self.auto_upgrade_ignore)

        # If Package Control is being upgraded, just do that and restart
        for package in packages:
            if package[0] != __name__:
                continue

            def reset_last_run():
                settings = sublime.load_settings(self.settings_file)
                settings.set('auto_upgrade_last_run', None)
                sublime.save_settings(self.settings_file)
            sublime.set_timeout(reset_last_run, 1)
            packages = [package]
            break

        if not packages:
            print '%s: No updated packages' % __name__
            return

        print '%s: Installing %s upgrades' % (__name__, len(packages))
        for package in packages:
            self.installer.manager.install_package(package[0])
            version = re.sub('^.*?(v[\d\.]+).*?$', '\\1', package[2])
            if version == package[2] and version.find('pull with') != -1:
                vcs = re.sub('^pull with (\w+).*?$', '\\1', version)
                version = 'latest %s commit' % vcs
            print '%s: Upgraded %s to %s' % (__name__, package[0], version)


class PackageCleanup(threading.Thread, PackageStartup):
    def __init__(self):
        self.manager = PackageManager()
        self.load_settings()
        threading.Thread.__init__(self)

    def run(self):
        found_pkgs = []
        installed_pkgs = self.installed_packages
        for package_name in os.listdir(sublime.packages_path()):
            package_dir = os.path.join(sublime.packages_path(), package_name)
            metadata_path = os.path.join(package_dir, 'package-metadata.json')

            # Cleanup packages that could not be removed due to in-use files
            cleanup_file = os.path.join(package_dir, 'package-control.cleanup')
            if os.path.exists(cleanup_file):
                try:
                    shutil.rmtree(package_dir)
                    print '%s: Removed old directory for package %s' % \
                        (__name__, package_name)
                except (OSError) as (e):
                    if not os.path.exists(cleanup_file):
                        open(cleanup_file, 'w').close()
                    print ('%s: Unable to remove old directory for package ' +
                        '%s - deferring until next start: %s') % (__name__,
                        package_name, str(e))

            # This adds previously installed packages from old versions of PC
            if os.path.exists(metadata_path) and \
                    package_name not in self.installed_packages:
                installed_pkgs.append(package_name)
                params = {
                    'package': package_name,
                    'operation': 'install',
                    'version': \
                        self.manager.get_metadata(package_name).get('version')
                }
                self.manager.record_usage(params)

            found_pkgs.append(package_name)

        sublime.set_timeout(lambda: self.finish(installed_pkgs, found_pkgs), 10)

    def finish(self, installed_pkgs, found_pkgs):
        self.save_packages(installed_pkgs)
        AutomaticUpgrader(found_pkgs).start()


# Start shortly after Sublime starts so package renames don't cause errors
# with keybindings, settings, etc disappearing in the middle of parsing
sublime.set_timeout(lambda: PackageCleanup().start(), 2000)

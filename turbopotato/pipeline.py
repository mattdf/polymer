import os
import json
from os.path import dirname, realpath
import subprocess

from .utils import sexyhash

WORKDIRS = os.path.join(dirname(dirname(__file__)), 'work')
if not os.path.exists(WORKDIRS):
    os.mkdir(WORKDIRS)

def workspace_for_repo(repo_url):
    sh = sexyhash(repo_url)
    pl = Workspace(os.path.join(WORKDIRS, sh))
    if not pl.exists('potato.json'):
        with pl.open('w', 'potato.json') as handle:
            handle.write(json.dumps({'repo_url': repo_url}))
        pl.reload()                
    return sh, pl

def workspace_by_name(name):
    return Workspace(os.path.join(WORKDIRS, name))

class Workspace:
    workdir:str
    _config:dict
    def __init__(self, workdir:str):
        self.workdir = realpath(workdir)        
        self.statedir = self.path('analyzer')
        for _ in [self.workdir, self.statedir]:
            if not os.path.exists(_):
                os.mkdir(_)
        self.reload()

    def path(self, *args):
        return os.path.join(self.workdir, *args)

    def exists(self, *args):
        return os.path.exists(self.path(*args))

    def open(self, mode, *args):
        return open(self.path(*args), mode)

    def reload(self):
        if self.exists('potato.json'):
            with self.open('r', 'potato.json') as handle:
                self._config = json.load(handle)
        else:
            self._config = dict()
        return self

    def config(self, k, v=None, unset=False, default=None):
        if k is None:
            return self._config
        if v is None:
            if unset:
                if k in self._config:
                    del self._config[k]
            else:
                return self._config.get(k, default)
        else:
            self._config[k] = v
            return v

    def git_clone(self):
        url = self.config('repo_url')
        if not self.exists('repo'):
            if url is None:
                raise RuntimeError('No repo_url set!')
            return self.shell(f"git clone --depth 1 '{url}' repo")
        return True

    def init(self, solfile):
        assert os.path.exists(solfile)
        self.shell('truffle init')
        targetfile = os.path.join(self.workdir, 'contracts', 'contract.sol')
        with open(solfile, 'rb') as inh:
            with open(targetfile, 'wb') as ouh:
                ouh.write(inh.read())

    def shell(self, shell_command):
        """
        Example: print(analyzer_exec('/tmp', 'ls -la /etc/'))
        """
        return subprocess.Popen([
            'docker', 'run',
            '--rm',  # Must remove, or it'll spam up docker
            '-u', f'{os.getuid()}:{os.getgid()}',
            '-v', f'{self.workdir}:/work',            
            '-h', 'polymerizer',
            '-e', 'HOME=/work',
            '-e', 'HISTFILESIZE=0',
            '-w', '/work',
            'polymerizer/analyzer:latest',
            '/bin/bash', '-c', shell_command
        ], stdout=subprocess.PIPE).communicate()[0]

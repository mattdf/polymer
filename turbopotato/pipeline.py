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
    pl = Workspace(sh, os.path.join(WORKDIRS, sh))
    if not pl.exists('potato.json'):
        with pl.open('w', 'potato.json') as handle:
            handle.write(json.dumps({'repo_url': repo_url}))
        pl.reload()                
    return sh, pl

def workspace_by_name(name):
    return Workspace(name, os.path.join(WORKDIRS, name))

def workspaces_list():
    for _ in os.listdir(WORKDIRS):
        if _[0] not in ('_', '.') and os.path.isdir(os.path.join(WORKDIRS, _)):
            yield _ 
class Workspace:
    workdir:str
    _config:dict
    def __init__(self, guid, workdir:str):
        self.guid = guid
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
        p = self.path(*args)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return open(p, mode)

    def reload(self):
        if self.exists('potato.json'):
            with self.open('r', 'potato.json') as handle:
                self._config = json.load(handle)
        else:
            self._config = dict()
        return self

    def config(self, k=None, v=None, unset=False, default=None):
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
        
    def run_codes(self, cid, codes:list[tuple[str,str]]):
        res = []
        if not len(codes):
            return
        if not self.exists('analyzer_harness.py'):
            with self.open('wb', 'analyzer_harness.py') as handle:
                with open(os.path.join(dirname(__file__), 'analyzer_harness.py'), 'rb') as ah:
                    handle.write(ah.read())
        for i, c in enumerate(codes):
            lang, code = c
            if 'z3.' in code and 'import z3' not in code:
                code = "import z3\n" + code
            print(code)
            if lang is None:
                lang = 'txt'
            path = ('analyzer', f'{cid}.{i}.{lang}')
            with self.open('w', *path) as handle:
                handle.write(code)
            if lang == 'python':
                stdout, stderr = self.shell('python3 ' + os.path.join(*path))
                if stdout is not None:
                    with self.open('wb', 'analyzer', f'{cid}.{i}.stdout') as handle:
                        handle.write(stdout)
                    stdout = stdout.decode()
                if stderr is not None:
                    with self.open('wb', 'analyzer', f'{cid}.{i}.stderr') as handle:
                        handle.write(stderr)
                    stderr = stderr.decode()
                harness_stdout, harness_stderr = self.shell('python3 analyzer_harness.py ' + os.path.join(*path))
                if harness_stdout is not None:
                    harness_stdout = harness_stdout.decode()
                if harness_stderr is not None:
                    harness_stderr = harness_stderr.decode()
            else:
                harness_stdout, harness_stderr = None, None
                stdout, stderr = None, None
            run = None
            if self.exists('analyzer', f'{cid}.{i}.{lang}.run'):
                with self.open('r', 'analyzer', f'{cid}.{i}.{lang}.run') as handle:
                    run = json.load(handle)
            res.append(dict(
                lang=lang,
                code=code,
                stdout=stdout,
                stderr=stderr,
                harness_stdout=harness_stdout,
                harness_stderr=harness_stderr,
                functions_return=run))
        return res

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
        ], stdout=subprocess.PIPE).communicate()

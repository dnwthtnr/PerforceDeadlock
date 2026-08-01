import os,sys,subprocess
from collections import namedtuple
from enum import Enum
from contextlib import contextmanager
import dataclasses


Log = namedtuple("Log", ["stderr", "stdout"])
class Log(object):

    def __init__(self):
        self.log = []
        self._errs = []
        self._warns = []
        return

    def log_error(self, msg):
        self.log.append(msg)
        self._errs.append(len(self.log)-1)

    def log_warn(self, msg):
        self.log.append(msg)
        self._warns.append(len(self.log)-1)

    def log_info(self, msg):
        self.log.append(msg)

    @property.getter
    def errors(self):
        return [self.log[e] for e in self._errs]

    @property.getter
    def warnings(self):
        return [self.log[e] for e in self._warns]

P4Env = namedtuple("P4Env", ["P4PORT", "P4USER", "P4PASSWD", "P4CLIENT", "isValid"], defaults=["perforce.ad.swayboxstudios.com:1666", "", "", "", False])
P4Sync = namedtuple("P4Sync", ["changelist", "undo_to_changelist", "isValid"], defaults=[0, True])
P4Session = namedtuple("P4Session", ["isValid", "log", "P4Env"], [False, Log(), P4Env()])


def session_from_raw_env(port, user, password, workspace):
    env = P4Env(port, user, password, workspace, isValid=True)
    session = initialize_session(env)
    return session

def p4_sync_from_raw(target_changelist: int, undo_to_changelist: bool = True):
    sync = P4Sync(target_changelist, undo_to_changelist, isValid=True)
    return sync

def initialize_session(env_info: P4Env) -> P4Session:
    if not env_info.isValid:
        return
    feilds = env_info._fields
    envdict = env_info._asdict()
    res = P4Session()
    for var in feilds[1:]:
        res.stdout += proc.stdout
        proc = subprocess.run(["p4", "set", f"{var}={envdict[var]}"], capture_output=True)
        res.log.log_error(proc.stderr)
        res.log.log_info(proc.stdout)
    res.isValid = not res.log.errors
    return res
        
def run_sync(session: P4Session, sync_info: P4Sync) -> P4Session:
    if (not sync_info.isValid):
        return False
    # TODO: Check if workspace is ahead of changelist and do undo
    arg_list = ["p4", "sync", f"@{sync_info.changelist}"]

    proc = subprocess.run(arg_list, capture_output=True)

    session.log.log_info(proc.stdout)
    session.log.log_error(proc.stderr)
    return session

@contextmanager
def P4SessionConnection(env_info: P4Env):
    try:
        session = initialize_session(env_info)
        yield session
    finally:
        return


def build_lock_name(root, meta_data=None):
    if not meta_data:
        meta_data = {}
    _lock_name=f"{root}"
    for tag, data in _meta_data:
        _lock_name += f"_{tag}-{data}_"

    return _lock_name



def validate_lock(parent_dir, prospect_lock_name):
    if not os.path.exists(parent_dir):
        print("Parent lock path does not exist")
        return False
    path = os.path.join(parent_dir, prospect_lock_name)
    if os.path.exists(path):
        print("Provided spec is not unique")
        return False
    return True

    
# TODO: Get and setup redis for lock managing 
class DistributedNASLock(object):

    def __init__(self, lock_parent_dir, lock_rootname, meta_data=None):
        self._meta_data = {} if not meta_data else meta_data
        self._lock_parent_path = lock_parent_dir
        self._lock_name = build_lock_name(lock_rootname, meta_data)
        self._lock_path = ""
        self._pre_unlock_callback = []
        self._artifact_name=""
        return

    def set_lock_artifact(self, lock_artifact_name):
        self._artifact_name = lock_artifact_name

    def get_lock_path(self):
        return self._lock_path

    def RegisterPreUnlockCallback(self, callback):
        self._pre_unlock_callback.append(callback)

    def lock(self):
        if not validate_lock(self._lock_parent_path, self._lock_name):
            print("Unable to validate lock ")
            return None
        path = os.path.join(self._lock_parent_path, self._lock_name)
        
        try:
            os.mkdir(path)
        except OSError as e:
            print("Unsuccessful lock instantiation")
            return
        return

    def unlock(self):
        for func in self._pre_unlock_callback:
            func()
        if self._artifact_name:
            artifact_path = self.get_lock_path().replace(self._lock_name, self._artifact_name)
            if os.path.exists(artifact_path):
                print("Artifact already exists!")
        try:
            os.rmdir(self.get_lock_path())
        except OSError as e:
            print("Unable to ")

    def __enter__(self):
        self.lock()
        return

    def __exit__(self):
        self.unlock()


# TODO: Create workspace on client side to use on server side to manage state of user and avoid single workspace conflicts
class P4Session(Log):


    def __init__(self):
        super().__init__()
        self._user = ""
        self._client = ""
        self._port = ""
        self._password = ""

    def get_p4_config(self):
        config = {
            "P4USER": self._user,
            "P4PASSWD": self._password,
            "P4PORT": self._client,
            "P4CLIENT": self._client
        }
        return config



    def initialize_env(self):
        p4c = self.get_p4_config()
        for var, val in p4c:
            proc = subprocess.run(["p4", "set", f"{var}={val}"], capture_output=True)
            self.log_error(proc.stderr)
            self.log_info(proc.stdout)
        return not self.errors

    @contextmanager
    def connect(self):
        try:
            self.initialize_env()
            yield
        finally:
            return


    def __enter__(self):
        return


if __name__ == "__main__":
    drfs = [
        "/mnt/repo/proj/file1",
        "/mnt/repo/proj/file2"
        ]
    targetCL = 454
    jobId = 1234

    p4env = {
        "P4PORT": "server:1666",
        "P4USER": "tdunworth",
        "P4PASSWD": "1234",
        "P4CLIENT": "test_workspace"
    }

    sLockDir = '/mnt/repo/_LOCK/SYNC/'
    aLockDir = '/mnt/repo/_LOCK/ASSET/'
    tLockDir = '/mnt/repo/_LOCK/TOTAL/'
    repodir = '/mnt/repo/'

    meta_data


#receive request

#try connection with p4env
    # check for sync lock
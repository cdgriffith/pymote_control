import os
import sys
from subprocess import Popen, run, PIPE
from datetime import datetime
import logging
from configparser import ExtendedInterpolation

import aiofiles
import reusables
from sanic import Sanic
from sanic.response import json
from box import Box, ConfigBox


class PCError(Exception):
    """Pymote Control Error"""

config = reusables.config_namespace(["pymote.ini", "config.ini"],
                                    interpolation=ExtendedInterpolation())
if not config:
    config = ConfigBox({'Pymote': {
        "io_dir": "io",
        "data_file": "data.json",
        "log_level": 10,
        "cleanup_on_start": True,
        "auth_type": "headers",
        "auth_tokens": "pass,password",
        "port": 6666,
        "host": "0.0.0.0",
        "log_file": "pymote_control.log"
    }})

log = reusables.setup_logger("pymote",
                             level=config.Pymote.int('log_level'),
                             file_path=os.path.expanduser(
                                 config.Pymote.log_file))

app = Sanic("pymote")

os.makedirs(config.Pymote.io_dir, exist_ok=True)
try:
    data = Box.from_json(filename=config.Pymote.data_file)
except FileNotFoundError:
    data = Box()
processes = Box()


@app.middleware('request')
async def check_auth(request):
    if config.Pymote.auth_type == "headers":
        token = request.headers.get('auth')
        if token not in config.Pymote.list('auth_tokens'):
            return json({'error': 'Not Authorized'}, status=403)


def still_running(pid):
    if data[pid].finished:
        return False
    if pid in processes:
        if processes[pid].poll() is not None:
            data[pid].finished = True
            data[pid].return_code = processes[pid].poll()
            return False
    elif sys.platform.startswith("linux"):
        resp = run(f"kill -0 {pid}", shell=True, stdout=PIPE, stderr=PIPE)
        if b"No such process" in resp.stderr:
            data[pid].finished = True
        return False
    return True


def cleanup_on_start():
    log.info("Cleaning up old data")
    delete = []
    for pid, info in data.items():
        if not still_running(pid):
            try:
                os.unlink(f"{info.base}_stdout")
                os.unlink(f"{info.base}_stderr")
                os.unlink(f"{info.base}_stdin")
            except OSError:
                log.exception(f"Could not clean up all {pid} files")
            delete.append(pid)
    for x in delete:
        del data[x]
    data.to_json(filename=config.Pymote.data_file)


async def start_program(command, **kwargs):
    file_base = f"{config.Pymote.io_dir}{os.sep}{datetime.utcnow().isoformat()}"
    reusables.touch(f"{file_base}_stdin")
    p = Popen(command, shell=True,
              stdout=open(f"{file_base}_stdout", "w"),
              stderr=open(f"{file_base}_stderr", "w"),
              stdin=open(f"{file_base}_stdin"),
              preexec_fn=os.setpgrp,
              **kwargs)
    data[str(p.pid)] = {"base": file_base,
                        "finished": False,
                        "log_pos": {"stdout": 0, "stderr": 0},
                        "return_code": None}
    data.to_json(filename=config.Pymote.data_file)
    processes[str(p.pid)] = p
    return str(p.pid)

async def read_file(pid, file, full=False):
    async with aiofiles.open(f"{data[pid].base}_{file}") as f:
        if not full:
            await f.seek(data[pid].log_pos[file])
        out = await f.read()
        data[pid].log_pos[file] = await f.tell()
    return out


@app.route("/v1/program/<pid>", methods=["GET"])
async def get_logs(request, pid):
    if pid not in data:
        return json({'error': f'PID {pid} does not exist'}, status=400)
    full = request.args.get('full', False)
    still_running(pid)
    stdout = await read_file(pid, "stdout", full=full)
    stderr = await read_file(pid, "stderr", full=full)
    data.to_json(filename=config.Pymote.data_file)
    return json({'stdout': stdout,
                 'stderr': stderr,
                 'finished': data[pid].finished,
                 'return_code': data[pid].return_code})


@app.route("/v1/program/", methods=["POST"])
async def new_program(request):
    pid = await start_program(request.json['command'])
    return json({'pid': pid})


@app.route("/v1/program/<pid>/stop", methods=["POST"])
async def stop_program(request, pid):
    if pid not in data:
        return json({'error': f'PID {pid} does not exist'}, status=400)
    if still_running(pid):
        if pid in processes:
            if processes[pid].poll() is not None:
                processes[pid].terminate()
                data[pid].return_code = processes[pid].returncode
                data[pid].finished = True
        elif sys.platform.startswith("linux"):
            resp = run(f"kill -9 {pid}")
            data[pid].finished = True
            log.info(f"Manually killing {pid} resulted "
                     f"in message {resp.stdout} {resp.stderr}")
        data.to_json(filename=config.Pymote.data_file)
    return json({'return_code': data[pid].return_code})


@app.route("/v1/program/<pid>", methods=["DELETE"])
async def stop_and_delete_logs(request, pid):
    if pid not in data:
        return json({'error': f'PID {pid} does not exist'}, status=400)
    if still_running(pid):
        if pid in processes:
            if processes[pid].poll() is not None:
                processes[pid].terminate()
                data[pid].finished = True
        elif sys.platform.startswith("linux"):
            resp = run(f"kill -9 {pid}")
            data[pid].finished = True
            log.info(f"Manually killing {pid} resulted "
                     f"in message {resp.stdout} {resp.stderr}")
    data.to_json(filename=config.Pymote.data_file)
    try:
        os.unlink(f"{data[pid].base}_stdout")
        os.unlink(f"{data[pid].base}_stderr")
        os.unlink(f"{data[pid].base}_stdin")
    except OSError:
        log.exception(f"Could not clean up all {pid} files")

    del data[pid]
    if pid in processes:
        return_code = processes[pid].returncode
        del processes[pid]
        return json({'return_code': return_code})
    return json({})


if __name__ == '__main__':
    # Remove the stupid logo
    sanic_log = logging.getLogger('sanic')
    sanic_log.setLevel(logging.INFO)

    log.info("Starting Pymote Control Center")
    log.debug(open(f"{os.path.dirname(os.path.realpath(__file__))}{os.sep}"
                   f"ascii_logo.txt").read())

    if config.Pymote.bool('cleanup_on_start'):
        cleanup_on_start()
    try:
        app.run(host=config.Pymote.host, port=config.Pymote.int('port'))
    finally:
        os._exit(0)

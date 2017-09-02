import os
from subprocess import run, Popen, PIPE

import pexpect
from flask import Flask, request
from box import Box


app = Flask(__name__)
io_dir = "io"
os.makedirs(io_dir, exist_ok=True)
try:
    data = Box.from_json(filename="data.json", default_box=True)
except FileNotFoundError:
    data = Box(default_box=True)


@app.route("/v1/program/<name>", methods=["POST"])
def new_program(name):
    data = request.get_json()
    cmd = data['command']
    cmmand_type = data.get('type', 'run')
    data[name].status = "New"
    file_base = f"{io_dir}{os.sep}{name}"
    p = Popen(cmd, shell=True,
              stdout=open(f"{file_base}_stdout.log", "w"),
              stderr=open(f"{file_base}_stderr.log", "w"),
              stdin=open(f"{file_base}_stdin.log"))





@app.route("/v1/program/<name>", methods=["DELETE"])
def end_program(name):
    pass




def execute_background_task():
    pass






if __name__ == '__main__':
    app.run()


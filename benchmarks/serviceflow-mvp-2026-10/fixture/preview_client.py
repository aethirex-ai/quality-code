#!/usr/bin/env python3
"""Sandbox-side bounded client; no browser process or network access needed."""
import argparse
import json
from pathlib import Path
import socket
import os
import time
import uuid
import stat


def request(socket_path, payload):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(75)
        sock.connect(str(socket_path))
        sock.sendall((json.dumps(payload)+"\n").encode())
        data = bytearray()
        while not data.endswith(b"\n"):
            chunk = sock.recv(4096)
            if not chunk:
                raise RuntimeError("broker disconnected")
            data.extend(chunk)
            if len(data) > 16384:
                raise RuntimeError("response exceeds limit")
        return json.loads(data)


def mailbox_request(workspace, payload):
    directory = Path(workspace)/".preview-mailbox"
    fd = os.open(directory, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    token = uuid.uuid4().hex
    request_name, response_name = token+".request", token+".response"
    temp_name = token+".pending"
    try:
        if len(os.listdir(fd)) > 100:
            raise RuntimeError("mailbox queue full")
        data = json.dumps(payload)
        if len(data.encode()) > 12288:
            raise RuntimeError("request exceeds limit")
        output_fd = os.open(temp_name, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600, dir_fd=fd)
        with os.fdopen(output_fd,"w") as dest:
            dest.write(data)
        os.rename(temp_name,request_name,src_dir_fd=fd,dst_dir_fd=fd)
        deadline = time.monotonic()+75
        while time.monotonic()<deadline:
            try:
                input_fd = os.open(response_name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
            except FileNotFoundError:
                time.sleep(0.05)
                continue
            with os.fdopen(input_fd,"rb") as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 16384:
                    raise RuntimeError("invalid response file")
                result = source.read(16385)
            if len(result)>16384:
                raise RuntimeError("response exceeds limit")
            return json.loads(result)
        raise RuntimeError("preview timed out after 75 seconds")
    finally:
        for name in (temp_name,request_name,response_name):
            try: os.unlink(name,dir_fd=fd)
            except FileNotFoundError: pass
        os.close(fd)

def read_actions(workspace, actions_file):
    components = actions_file.split("/")
    if any(not x or x.startswith(".") or "\\" in x or ":" in x for x in components):
        raise ValueError("actions-file must be a workspace-relative path")
    fd = os.open(workspace,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for component in components[:-1]:
            next_fd=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd)
            fd=next_fd
        file_fd=os.open(components[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        with os.fdopen(file_fd,"rb") as source:
            info=os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size>8192 or info.st_nlink != 1:
                raise RuntimeError("invalid actions file")
            raw=source.read(8193)
        if len(raw)>8192:
            raise RuntimeError("actions file exceeds limit")
        return json.loads(raw)
    finally:
        os.close(fd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--transport", choices=("mailbox","unix"), default="mailbox")
    parser.add_argument("--socket", type=Path, default=Path.cwd()/".preview.sock")
    parser.add_argument("--actions-file", help="workspace-relative JSON list of safe actions")
    parser.add_argument("--ready", action="store_true")
    parser.add_argument("--page", default="/")
    parser.add_argument("--viewport", type=int, choices=(375,1440), default=1440)
    args = parser.parse_args()
    payload = {"op":"ready"} if args.ready else {"op":"render","page":args.page,"viewport":args.viewport}
    if args.actions_file:
        if args.ready:
            parser.error("ready does not accept actions")
        payload["actions"] = read_actions(args.workspace,args.actions_file)
    result = mailbox_request(args.workspace,payload) if args.transport=="mailbox" else request(args.socket,payload)
    print(json.dumps(result))
    raise SystemExit(0 if result.get("ok") else 1)

if __name__ == "__main__":
    main()

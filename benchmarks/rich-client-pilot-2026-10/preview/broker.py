#!/usr/bin/env python3
"""Fixed-root, bounded AF_UNIX visual preview broker."""
import argparse
import base64
import tempfile
import stat
import json
import os
from pathlib import Path
import socketserver
import subprocess
import threading
import time
import re
from datetime import datetime, timezone
import uuid
from urllib.parse import unquote, urlsplit

MAX_REQUEST = 4096
ALLOWED_KEYS = {"op", "page", "viewport", "actions"}

def validate_request(request, root):
    if not isinstance(request, dict) or set(request) - ALLOWED_KEYS:
        raise ValueError("unknown request fields")
    if request.get("op") == "ready":
        if set(request) != {"op"}:
            raise ValueError("ready takes no arguments")
        return None
    if request.get("op") != "render":
        raise ValueError("unknown operation")
    actions = request.get("actions", [])
    if not isinstance(actions, list) or len(actions) > 12:
        raise ValueError("actions must be a list of at most 12 items")
    for action in actions:
        if not isinstance(action, dict) or set(action) - {"op","selector","value"}:
            raise ValueError("invalid action fields")
        op, selector = action.get("op"), action.get("selector")
        if op not in {"click","fill","select","check","press","scroll"}:
            raise ValueError("unsupported action")
        if not isinstance(selector,str) or not selector or len(selector)>200:
            raise ValueError("action selector must be 1-200 characters")
        if op in {"fill","select","press"}:
            value=action.get("value")
            if not isinstance(value,str) or len(value)>300:
                raise ValueError("action value must be a string of at most 300 characters")
            if op=="press" and value not in {"Tab","Escape","Enter"}:
                raise ValueError("press supports only Tab, Escape, Enter")
        elif "value" in action:
            raise ValueError("click/check/scroll take no value")
    width = request.get("viewport")
    if type(width) is not int or width not in (375, 1440):
        raise ValueError("viewport must be 375 or 1440")
    page = request.get("page", "index.html")
    if not isinstance(page, str) or not page or len(page) > 512:
        raise ValueError("invalid page")
    decoded = unquote(page)
    parts = decoded.split("/")
    if (urlsplit(decoded).scheme or urlsplit(decoded).netloc or decoded.startswith("/")
            or "\\" in decoded or "?" in decoded or "#" in decoded
            or any(not x or x.startswith(".") or ":" in x for x in parts)
            or not decoded.endswith(".html")):
        raise ValueError("page must be a relative local HTML path")
    target = root.joinpath(decoded).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError("page unavailable in this workspace")
    return decoded, width

class Broker(socketserver.UnixStreamServer):
    def __init__(self, root, socket_path, node, module, bind_socket=True):
        self.root = root.resolve(strict=True)
        self.root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.node, self.module = node, module
        self.renderer = Path(__file__).with_name("render.mjs").resolve()
        socket_path = Path(socket_path).absolute()
        if socket_path.parent.resolve() != self.root or socket_path.is_symlink():
            raise ValueError("socket must be directly inside workspace root")
        self.out = self.root / ".preview-output"
        if self.out.is_symlink():
            raise ValueError("output may not be a symlink")
        self.out.mkdir(exist_ok=True, mode=0o700)
        if self.out.resolve().parent != self.root:
            raise ValueError("output must remain inside root")
        # Never remove an existing socket/file owned by another process.
        self.bound_socket = bind_socket
        if bind_socket:
            super().__init__(str(socket_path), Handler)
            os.chmod(socket_path, 0o600)
        self.ready = False
        self.request_timeout = 30

    def call_renderer(self, request):
        args = [self.node, str(self.renderer)]
        payload = dict(request, module=self.module)
        if request["op"] == "render":
            assets = {}
            total = 0
            allowed = {".html", ".css", ".js", ".mjs", ".json", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".ico", ".woff", ".woff2", ".ttf"}
            def collect(fd, prefix="", depth=0):
                nonlocal total
                if depth > 12:
                    return
                for name in os.listdir(fd):
                    if name.startswith(".") or ":" in name or "\\" in name:
                        continue
                    try:
                        child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                    except OSError:
                        continue
                    try:
                        info = os.fstat(child)
                        relative = prefix + name
                        if stat.S_ISDIR(info.st_mode):
                            collect(child, relative + "/", depth + 1)
                        elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and Path(name).suffix.lower() in allowed:
                            if info.st_size > 12 * 1024 * 1024 or total + info.st_size > 64 * 1024 * 1024 or len(assets) >= 500:
                                raise ValueError("static asset snapshot exceeds limits")
                            with os.fdopen(os.dup(child), "rb") as source:
                                content = source.read(12 * 1024 * 1024 + 1)
                            total += len(content)
                            if total > 64 * 1024 * 1024 or len(content) > 12 * 1024 * 1024:
                                raise ValueError("static asset snapshot exceeds limits")
                            assets[relative] = base64.b64encode(content).decode()
                    finally:
                        os.close(child)
            collect(self.root_fd)
            if request["page"] not in assets:
                raise ValueError("page unavailable in static snapshot")
            payload["assets"] = assets
        result = subprocess.run(args, input=json.dumps(payload), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25,
            env={k:v for k,v in os.environ.items() if k in
                 {"PATH", "HOME", "TMPDIR", "PLAYWRIGHT_BROWSERS_PATH", "LANG"}})
        if result.returncode:
            raise RuntimeError("renderer failed: " + result.stderr[-1200:])
        if len(result.stdout) > 16384:
            raise RuntimeError("renderer response too large")
        return json.loads(result.stdout)

    def check_ready(self):
        self.call_renderer({"op":"check"})
        self.ready = True

def process_request(server, request):
    try:
        validated = validate_request(request, server.root)
        if not server.ready:
            raise ValueError("broker not ready")
        if validated is None:
            response = {"ok":True, "ready":True, "viewports":[375,1440]}
        else:
            page, width = validated
            out = server.out
            if out.is_symlink() or out.resolve().parent != server.root:
                raise ValueError("output directory changed")
            name = uuid.uuid4().hex + ".png"
            screenshot = out / name
            with tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix="render-") as staging:
                staged = Path(staging)/"preview.png"
                response = server.call_renderer({"op":"render", "page":page,
                    "viewport":width, "screenshot":str(staged), "actions":request.get("actions",[])})
                out_fd = os.open(".preview-output", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=server.root_fd)
                try:
                    image_fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=out_fd)
                    with os.fdopen(image_fd, "wb") as dest:
                        dest.write(staged.read_bytes())
                finally:
                    os.close(out_fd)
            response["screenshot"] = str(screenshot)
            response["ok"] = True
    except Exception as exc:
        response = {"ok":False, "error":str(exc)[:1500]}
    if isinstance(request,dict) and request.get("op")=="render":
        try:
            record_preview(server,request,response)
        except Exception as exc:
            response={"ok":False,"error":"preview history failed: "+str(exc)[:500]}
    return response

def record_preview(server, request, response):
    screenshot = response.get("screenshot")
    if screenshot:
        try: screenshot = str(Path(screenshot).relative_to(server.root))
        except ValueError: screenshot = None
    event = {"timestamp":datetime.now(timezone.utc).isoformat(),
        "request":{key:request.get(key) for key in ("page","viewport","actions") if key in request},
        "result":{key:response[key] for key in ("ok","error","errors","horizontalOverflow","actionResults") if key in response}}
    if screenshot:
        event["result"]["screenshot"] = screenshot
    encoded=json.dumps(event,ensure_ascii=False).encode()+b"\n"
    if len(encoded)>16384:
        event={"timestamp":event["timestamp"],"request":{"metadataOmitted":"exceeds event limit"},
            "result":{"ok":response.get("ok"),"metadataOmitted":"exceeds event limit"}}
        encoded=json.dumps(event).encode()+b"\n"
    fd=os.open(".preview-events.jsonl",os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW|os.O_NONBLOCK,0o600,dir_fd=server.root_fd)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("invalid preview history file")
        if info.st_size+len(encoded)>16*1024*1024:
            raise ValueError("preview history full; archive before restart")
        if os.write(fd,encoded)!=len(encoded):
            raise RuntimeError("incomplete preview history write")
    finally:
        os.close(fd)

def encode_response(response):
    encoded=json.dumps(response,ensure_ascii=False).encode()
    if len(encoded)>16383:
        return b'{"ok":false,"error":"response metadata exceeds limit"}'
    return encoded

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(5)
        try:
            line = self.rfile.readline(MAX_REQUEST + 1)
            if len(line) > MAX_REQUEST or not line.endswith(b"\n"):
                raise ValueError("request exceeds limit or lacks newline")
            response = process_request(self.server, json.loads(line))
        except Exception as exc:
            response = {"ok":False, "error":str(exc)[:1500]}
        self.wfile.write(encode_response(response)+b"\n")

def serve_mailbox(server, stop_event=None):
    name = ".preview-mailbox"
    try:
        os.mkdir(name, mode=0o700, dir_fd=server.root_fd)
    except FileExistsError:
        pass
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=server.root_fd)
    try:
        while stop_event is None or not stop_event.is_set():
            entries = sorted(os.listdir(fd))
            requests = [x for x in entries if re.fullmatch(r"[0-9a-f]{32}\.request", x)]
            if len(entries) > 200:
                raise ValueError("mailbox resource limit: clean stale files before restart")
            for filename in requests[:8]:
                try:
                    source_fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                    with os.fdopen(source_fd, "rb") as source:
                        info = os.fstat(source.fileno())
                        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_REQUEST:
                            raise ValueError("invalid request file")
                        data = source.read(MAX_REQUEST+1)
                    if len(data) > MAX_REQUEST:
                        raise ValueError("request too large")
                    response = process_request(server, json.loads(data))
                except Exception as exc:
                    response = {"ok":False,"error":str(exc)[:1500]}
                response_name = filename.replace(".request", ".response")
                temp_name = uuid.uuid4().hex + ".pending"
                output_fd = os.open(temp_name, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600, dir_fd=fd)
                with os.fdopen(output_fd,"wb") as dest:
                    dest.write(encode_response(response))
                os.rename(temp_name,response_name,src_dir_fd=fd,dst_dir_fd=fd)
                os.unlink(filename,dir_fd=fd)
            time.sleep(0.05)
    finally:
        os.close(fd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", "--workspace", dest="root", type=Path, required=True)
    parser.add_argument("--transport", choices=("mailbox","unix"), default="mailbox")
    parser.add_argument("--socket", type=Path)
    parser.add_argument("--node", default=os.environ.get("PREVIEW_NODE", "node"))
    parser.add_argument("--playwright-module", default=os.environ.get("PREVIEW_PLAYWRIGHT_MODULE", "playwright"))
    args = parser.parse_args()
    socket_path = args.socket or args.root / ".preview.sock"
    server = Broker(args.root, socket_path, args.node, args.playwright_module, bind_socket=args.transport=="unix")
    try:
        server.check_ready()
        print(json.dumps({"ready":True,"transport":args.transport,"workspace":str(server.root)}), flush=True)
        if args.transport == "mailbox":
            serve_mailbox(server)
        else:
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        os.close(server.root_fd)
        if server.bound_socket:
            server.server_close()
            Path(socket_path).unlink(missing_ok=True)

if __name__ == "__main__":
    main()

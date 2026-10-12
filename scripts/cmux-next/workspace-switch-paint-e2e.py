#!/usr/bin/env python3
"""A workspace switch paints in one step on a running tagged build (motion pass, 2026-10-12).

Cmd-1 to Cmd-9, the palette and `cmux workspace select` switch workspaces. The window swaps the
content area, and the sidebar moves its selection fill to the new row. Both change in the same
frame: read frame after frame around the key, or around the action run through the control
router as the palette and the CLI run it (`debug.new_tab` frame_strip), everything outside the
pane's content area equals the frame before the switch or the settled one. Through the router,
a cold switch (to a workspace this window never showed, whose content it builds then) drew
the new content a frame or two before the row's fill moved.
Blank content frames are reported, not failed: a terminal shown for the first time draws its
screen once it attaches.

The app runs already (a capture slot: `capture-host launch`), with its debug socket.

Usage: workspace-switch-paint-e2e.py --socket <path> [--out DIR]
"""
import argparse, json, socket, sys, time

parser = argparse.ArgumentParser()
parser.add_argument("--socket", required=True)
parser.add_argument("--out", default="/tmp/workspace-switch-paint", help="where the app writes each switch's frames")
parser.add_argument("--duration-ms", type=float, default=500)
opts = parser.parse_args()


def rpc(method, params=None, timeout=30):
    try:
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        conn.settimeout(timeout)
        conn.connect(opts.socket)
        conn.sendall((json.dumps({"id": 1, "method": method, "params": params or {}}) + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = conn.recv(1 << 20)
            if not chunk:
                break
            buf += chunk
        conn.close()
        reply = json.loads(buf)
        return reply.get("result") if reply.get("ok") else {"error": reply.get("error")}
    except (OSError, ValueError) as error:
        return {"error": str(error)}


def workspace_rows():
    rows = ((rpc("debug.sidebar_rows") or {}).get("windows") or [{}])[0].get("rows") or []
    return [r for r in rows if str(r.get("key", "")).startswith("workspace")]


if not workspace_rows() and "error" in (rpc("debug.windows") or {}):
    sys.exit("FAIL the app does not answer on " + opts.socket)
rpc("debug.motion", {"action": "speed", "value": "fast"})
# Workspaces added at the bottom are listed, not shown: each one's first switch is cold.
while len(workspace_rows()) < 8:
    rpc("action.run", {"action": "workspace.newAtBottom"})
    time.sleep(0.5)  # test harness wait: one workspace at a time
rpc("action.run", {"action": "selectWorkspaceByNumber", "args": {"index": 1}})
time.sleep(1.0)  # test harness wait: the first workspace shows

failures = []
# Cold: 3 to 8 were never shown. Warm: switches back to ones shown (parked).
switches = [("key", "cold", 3), ("key", "cold", 4), ("run", "cold", 5), ("run", "cold", 6), ("run", "cold", 7), ("run", "cold", 8),
            ("key", "warm", 1), ("key", "warm", 3), ("run", "warm", 4), ("run", "warm", 5), ("run", "warm", 1), ("run", "warm", 6)]
for via, kind, digit in switches:
    time.sleep(0.6)  # test harness wait: the window settles before the strip
    out = f"{opts.out}/{via}-{kind}-{digit}"
    trigger = {"key": str(digit)} if via == "key" else {"run": {"action": "selectWorkspaceByNumber", "args": {"index": digit}}}
    reply = rpc("debug.new_tab", {"action": "frame_strip", "dir": out, "duration_ms": opts.duration_ms, **trigger}) or {}
    if "error" in reply:
        sys.exit(f"FAIL frame_strip {via} {digit}: {reply}")
    bad = [f for f in reply["frames"] if f["intermediate"]]
    print(f"{via} {digit} ({kind}): {reply['frame_count']} frames every {reply['mean_interval_ms']:.1f} ms, "
          f"intermediate={reply['intermediate']:.0f} blank={reply['blank']:.0f} strip={out}/strip.png", flush=True)
    for frame in bad:
        print(f"  {frame['file']} at {frame['ms']:+.0f} ms: outside differs {frame['outside_vs_before']:.3f} from before, "
              f"{frame['outside_vs_final']:.3f} from final", flush=True)
    if bad:
        failures.append(f"{via} {digit} ({kind})")

if failures:
    sys.exit(f"FAIL intermediate frames (the content and the sidebar selection changed apart): {', '.join(failures)}")
print("PASS every switch changed the window in one step")

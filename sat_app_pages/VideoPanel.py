
import re
import json

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QButtonGroup, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget
)

PLAYER_HTML = """<html><body style="margin:0;background:#000">
<iframe id="yt" src="__SRC__" style="position:absolute;inset:0;width:100%;height:100%;border:0"
  allow="autoplay; encrypted-media; picture-in-picture"
  referrerpolicy="strict-origin-when-cross-origin"></iframe>
<div id="cover" style="position:absolute;inset:0;display:none;align-items:center;justify-content:center;
  background:#e9ecf5;color:#000;font:600 16px sans-serif;text-align:center;padding:16px"></div>
<script>
var VOL = 100;
var RATE = 1.0;
var cur = __MODE__;

function cmd(f, a) {
    document.getElementById("yt").contentWindow.postMessage(
        JSON.stringify({
            event: "command",
            func: f,
            args: a === undefined ? [] : a
        }),
        "*"
    );
}

function tune(m) {
    if (m === "video" || m === "audio") {
        cmd("unMute", []);
        cmd("setVolume", [VOL]);
        cmd("setPlaybackRate", [RATE]);
    }
}

function cover(m) {
    var c = document.getElementById("cover");

    if (m === "audio") {
        c.textContent = "Audio only";
        c.style.display = "flex";
    } else if (m === "pause") {
        c.textContent = "Paused during hard questions";
        c.style.display = "flex";
    } else if (m === "off") {
        c.textContent = "Video is off";
        c.style.display = "flex";
    } else {
        c.style.display = "none";
    }
}

function setMode(m) {
    cur = m;
    cover(m);

    console.log("Setting video mode:", m);

    if (m === "off" || m === "pause") {
        // Mute immediately so audio cannot leak into off conditions
        cmd("mute", []);
        cmd("pauseVideo", []);
    } else if (m === "video" || m === "audio") {
        cmd("setVolume", [100]);
        cmd("unMute", []);
        cmd("setPlaybackRate", [1.0]);
        cmd("playVideo", []);
    }
}

cover(cur);
// The YouTube player needs a moment to start listening, so apply volume/speed a few times after load.
function applySettingsSoon(){[500,1500,3000,6000].forEach(function(t){setTimeout(function(){tune(cur);},t);});}
document.getElementById("yt").addEventListener("load",applySettingsSoon);
applySettingsSoon();

function onPlayerReady(event) {
    const p = event.target;

    console.log("PLAYER READY");
    console.log("Initially muted:", p.isMuted());

    p.unMute();
    p.setVolume(100);

    console.log("After unmute:", p.isMuted());

    setTimeout(() => {
        console.log("After 1 second:", p.isMuted());
        console.log("Volume:", p.getVolume());
        console.log("Playback state:", p.getPlayerState());
    }, 1000);
};

function debugPlayer(label) {
    if (typeof player === "undefined" || !player) return;

    console.log(
        label,
        "Muted:", player.isMuted(),
        "Volume:", player.getVolume(),
        "State:", player.getPlayerState()
    );
};
</script></body></html>"""


class VideoPanel(QWidget):
    """YouTube player shown beside the questions, with on-screen always-on / always-off buttons."""

    setting_changed = pyqtSignal(str)   # "follow" | "on" | "off"

    def __init__(self, mode="off"):
        super().__init__()
        self.setObjectName("videoPanel")
        self.setMinimumWidth(380)
        self.mode = mode  

        # Segmented control: should the video follow the question difficulty, or always be on / off?
        self.setting_group = QButtonGroup(self)
        self.setting_group.setExclusive(True)
        self.setting_buttons = {"follow": "By difficulty", "on": "Always on", "off": "Always off",
                                        "half": "Test: half on, half off (random order)"}
        seg = QGridLayout()
        seg.addWidget(QLabel("Video:"), 0, 0)

        self.view = QWebEngineView()
        self.view.setPage(DebugWebEnginePage(self.view))
        self.view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        self.view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.view.page().fullScreenRequested.connect(lambda req: req.reject())
        self.stop()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        header = QHBoxLayout()
        header.addWidget(QLabel("YouTube player"))
        header.addStretch(1)
        layout.addLayout(header)
        layout.addLayout(seg)
        layout.addWidget(self.view, 1)

    def youtube_embed_url(self, text: str):
        """Turn a pasted YouTube link / ID into an embeddable URL (or None)."""
        text = text.strip()
        if not text:
            return None
        m_list = re.search(r"[?&]list=([\w-]+)", text)
        m_vid = re.search(r"(?:v=|youtu\.be/|/embed/|/shorts/|/live/)([\w-]{11})", text)
        if m_vid:
            url = f"https://www.youtube.com/embed/{m_vid.group(1)}?autoplay=1&rel=0"
            if m_list:
                url += f"&list={m_list.group(1)}"
            return url
        if m_list:
            return f"https://www.youtube.com/embed/videoseries?list={m_list.group(1)}&autoplay=1"
        if re.fullmatch(r"[\w-]{11}", text):
            return f"https://www.youtube.com/embed/{text}?autoplay=1&rel=0"
        return None

    def play(self):
        src = self.youtube_embed_url("https://youtu.be/4hiENsNt6pU?si=Y-SMCXd1xA-SGlGp")

        if not src:
            self.show_message("That doesn't look like a YouTube link.")
            return
        
        #src = src.split("?")[0]
        
        # autoplay runs based on current mode
        autoplay = 0 if self.mode in ("pause", "off") else 1

        print(f"MODE = {self.mode}, AUTOPLAY = {autoplay}")
        # separator = "&" if "?" in src else "?"

        src += (
            f"autoplay={autoplay}"
            f"&mute={not autoplay}"
            "&playsinline=1"
            "&enablejsapi=1"
            "&origin=https%3A%2F%2Flocalhost"
        )
        print(src)

        html = PLAYER_HTML.replace("__SRC__", src).replace("__MODE__", json.dumps(self.mode))

        self.view.page().setAudioMuted(False)

        print("Loading PLAYER_HTML", flush=True)
        print("Contains debug logging:", "PLAYER READY" in html, flush=True)
        print("HTML length:", len(html), flush=True)
        self.view.setHtml(html, QUrl("https://localhost/"))

        self.has_video = True

    def set_mode(self, mode):
        """Switch between video / audio-only / paused / off (only acts on a change)."""
        if mode == self.mode:
            return
        self.mode = mode
        #self.status.setText(MODE_LABEL[mode])
        self.view.page().runJavaScript(f'if (typeof setMode === "function") setMode("{mode}");')

    def stop(self):
        self.has_video = False
        self.show_message("Paste a YouTube link above and press Play.")

    def show_message(self, msg):
        self.view.setHtml(
            '<body style="margin:0;background:#111;color:#aaa;font:14px sans-serif;'
            f'display:flex;align-items:center;justify-content:center;height:100vh">{msg}</body>')
        
class DebugWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"[JS] {message} (line {lineNumber})", flush=True)
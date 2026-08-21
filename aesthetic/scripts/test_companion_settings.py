"""Pure companion contracts for rank provenance and theme settings."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class HelperRankProvenanceTest(unittest.TestCase):
    def run_node(self, source: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["node", "-e", source], capture_output=True, text=True)

    def test_unscored_rows_do_not_send_a_rank_with_sentiment(self) -> None:
        helper = json.dumps(str(ROOT / "companion" / "helper.js"))
        source = (
            f"const h=require({helper});"
            "if(h.starsForEvent(0,'no')!==null)process.exit(1);"
            "if(h.starsForEvent(0,'yes')!==0)process.exit(2);"
            "if(h.starsForEvent(5,'yes')!==5)process.exit(3);"
        )
        completed = self.run_node(source)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_zero_control_is_only_on_for_an_explicit_zero(self) -> None:
        helper = json.dumps(str(ROOT / "companion" / "helper.js"))
        source = (
            f"const h=require({helper});"
            "if(!h.rankIsOn(0,0)||h.rankIsOn(0,5)||!h.rankIsOn(5,5))process.exit(1);"
        )
        completed = self.run_node(source)
        self.assertEqual(completed.returncode, 0, completed.stderr)


class FrameSettingsStructureTest(unittest.TestCase):
    def test_frame_header_does_not_duplicate_article_theme_controls(self) -> None:
        frame = (ROOT / "companion" / "frame-template.html").read_text(encoding="utf-8")
        self.assertNotIn('data-theme-settings', frame)
        self.assertNotIn('data-follow-art-direction', frame)


class ServerThemeSafetyTest(unittest.TestCase):
    def test_white_on_white_rolls_back_the_offending_background(self) -> None:
        server = json.dumps(str(ROOT / "companion" / "server.cjs"))
        source = (
            f"const s=require({server});"
            "const x=s.validateThemeElements("
            "{bg:'#ffffff',ink:'#ffffff',accent:'#eeeeee',font:'system-ui'},"
            "{bg:'#111111',ink:'#ffffff',accent:'#73d2ff',font:'system-ui'});"
            "if(x.active.bg!=='#111111'||x.active.ink!=='#ffffff')process.exit(1);"
            "if(s.contrast(x.active.bg,x.active.ink)<4.5)process.exit(2);"
        )
        completed = subprocess.run(["node", "-e", source], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


class ServerLiveStateTest(unittest.TestCase):
    def test_polling_keeps_reload_alive_when_native_watching_hits_emfile(self) -> None:
        """macOS can exhaust file descriptors while the design agent is busy.

        The companion must degrade to a small directory scan instead of staying
        connected while silently serving a stale article.
        """
        server = json.dumps(str(ROOT / "companion" / "server.cjs"))
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "ranking.html").write_text("one", encoding="utf-8")
            source = (
                f"const s=require({server});const fs=require('fs');"
                "const {EventEmitter}=require('events');"
                f"const dir={json.dumps(tmp)};"
                "const badWatch=()=>{const w=new EventEmitter();w.close=()=>{};"
                "setTimeout(()=>{const e=new Error('too many open files');"
                "e.code='EMFILE';w.emit('error',e)},5);return w};"
                "let changed=false;"
                "const watcher=s.startContentWatcher(dir,()=>{changed=true},"
                "{watch:badWatch,pollMs:20,log:()=>{}});"
                "setTimeout(()=>fs.writeFileSync(dir+'/ranking.html','two'),35);"
                "setTimeout(()=>{watcher.close();process.exit(changed?0:2)},180);"
            )
            completed = subprocess.run(
                ["node", "-e", source], capture_output=True, text=True, timeout=3)
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

    def test_live_replay_ignores_rank_carried_by_sentiment(self) -> None:
        server = json.dumps(str(ROOT / "companion" / "server.cjs"))
        events = json.dumps(
            '{"type":"sentiment","element":"core.idea","sentiment":"like","stars":0}\n'
            '{"type":"rank","element":"core.idea","stars":4}\n'
            '{"type":"sentiment","element":"core.idea","sentiment":"dislike","stars":0}\n'
        )
        source = (
            f"const s=require({server});const x=s.reduceSignals({events});"
            "if(x['core.idea'].stars!==4||x['core.idea'].sentiment!=='dislike')process.exit(1);"
        )
        completed = subprocess.run(["node", "-e", source], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()

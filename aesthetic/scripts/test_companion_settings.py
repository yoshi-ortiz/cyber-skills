"""Pure companion contracts for rank provenance and theme settings."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

import bootstrap_harness as bh


ROOT = Path(__file__).parents[1]


class Node:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]], parent: "Node | None"):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children: list[Node] = []
        self.text: list[str] = []

    def find(self, **attrs: str) -> "Node | None":
        if all(name in self.attrs and (self.attrs.get(name) or "") == value
               for name, value in attrs.items()):
            return self
        for child in self.children:
            found = child.find(**attrs)
            if found:
                return found
        return None

    def all(self, tag: str) -> list["Node"]:
        found = [self] if self.tag == tag else []
        for child in self.children:
            found.extend(child.all(tag))
        return found

    def visible_text(self) -> str:
        if "dh-sr-only" in self.attrs.get("class", "").split():
            return ""
        return " ".join("".join(self.text).split() + [
            text for child in self.children if (text := child.visible_text())
        ]).strip()


class TreeParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
            "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__()
        self.root = Node("root", [], None)
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in self.VOID:
            self.current = node

    def handle_endtag(self, tag: str) -> None:
        node = self.current
        while node.parent and node.tag != tag:
            node = node.parent
        if node.parent:
            self.current = node.parent

    def handle_data(self, data: str) -> None:
        self.current.text.append(data)


def tree(markup: str) -> Node:
    parser = TreeParser()
    parser.feed(markup)
    return parser.root


def declarations(style: str, selector: str) -> dict[str, str]:
    style = re.sub(r"/\*.*?\*/", "", style, flags=re.S)
    body = next((body for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", style)
                 if selector in [item.strip() for item in selectors.split(",")]), None)
    if body is None:
        return {}
    return {
        name.strip(): value.strip()
        for item in body.split(";") if ":" in item
        for name, value in [item.split(":", 1)]
    }


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

    def test_runtime_status_parser_separates_the_emoji_from_wrapping_copy(self) -> None:
        helper = json.dumps(str(ROOT / "companion" / "helper.js"))
        source = (
            f"const h=require({helper});"
            "const x=h.splitStatusParts('🎨 Redrawing the cover for mobile');"
            "if(x.icon!=='🎨'||x.text!=='Redrawing the cover for mobile')process.exit(1);"
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

    def test_frame_owns_the_invariant_header_dom_and_typography(self) -> None:
        frame = (ROOT / "companion" / "frame-template.html").read_text(encoding="utf-8")
        document = tree(frame)
        header = document.find(**{"data-companion-header": ""})
        self.assertIsNotNone(header)
        self.assertIsNotNone(header.find(**{"data-agent-app": ""}))
        self.assertIsNotNone(header.find(**{"data-agent-model": ""}))
        self.assertIsNotNone(header.find(**{"data-connection-text": ""}))
        style = "\n".join(node.visible_text() for node in document.all("style"))
        header_rule = declarations(style, ".header")
        self.assertIn("font-family", header_rule)
        self.assertNotIn("--dh-font", header_rule["font-family"])
        brand_rule = declarations(style, ".dh-brand")
        self.assertEqual(brand_rule.get("display"), "grid")
        self.assertIn("grid-template-columns", brand_rule)

    def test_saved_font_updates_the_app_but_not_the_invariant_header(self) -> None:
        helper = (ROOT / "companion" / "helper.js").read_text(encoding="utf-8")
        frame = (ROOT / "companion" / "frame-template.html").read_text(encoding="utf-8")
        self.assertIn("root.setProperty('--app-font', elements.font)", helper)
        self.assertIn("'--app-font'", helper)
        self.assertIn("font-family: var(--app-font)", frame)
        header = re.search(r"\.header\s*\{(?P<body>.*?)\n\s*\}", frame, re.S)
        self.assertIsNotNone(header)
        self.assertNotIn("var(--app-font)", header.group("body"))


class ArticleSettingsStructureTest(unittest.TestCase):
    def markup(self, status: str = "", working: bool = False) -> str:
        decisions = {
            "version": bh.VERSION, "state": "draft", "supersededCount": 0,
            "elements": [{
                "element": "core.idea", "stars": 0, "sentiment": None,
                "state": "proposed", "scored": False, "source": "agent",
            }],
        }
        return bh.render_article(Path("/tmp"), decisions, {"core.idea"}, "", "en", None,
                                 "Project", "Ask.", status, agent_working=working)

    def test_bottom_settings_have_exact_control_vocabulary_and_a_semantic_switch(self) -> None:
        document = tree(self.markup())
        settings = document.find(**{"data-theme-settings": ""})
        self.assertIsNotNone(settings)
        self.assertNotIn("open", settings.attrs)
        self.assertEqual(settings.visible_text(),
                         "Agent settings Update app theme Saved themes Reset theme Save")
        switch = settings.find(**{"data-follow-art-direction": ""})
        self.assertEqual(switch.tag, "input")
        self.assertEqual(switch.attrs.get("type"), "checkbox")
        self.assertEqual(switch.attrs.get("role"), "switch")
        labels = {node.attrs.get("for"): node.visible_text() for node in settings.all("label")}
        self.assertEqual(labels.get(switch.attrs.get("id")), "Update app theme")
        select = settings.find(**{"data-theme-select": ""})
        self.assertEqual(labels.get(select.attrs.get("id")), "Saved themes")
        buttons = [button.visible_text() for button in settings.all("button")]
        self.assertEqual(buttons, ["Reset theme", "Save"])

    def test_spanish_settings_panel_is_spanish_not_english(self) -> None:
        """One screen speaking two languages is the exact regression
        STRINGS was built to prevent, and this panel had drifted back into
        it -- hardcoded English literals bypassing STRINGS entirely."""
        decisions = {
            "version": bh.VERSION, "state": "draft", "supersededCount": 0,
            "elements": [{
                "element": "core.idea", "stars": 0, "sentiment": None,
                "state": "proposed", "scored": False, "source": "agent",
            }],
        }
        markup = bh.render_article(Path("/tmp"), decisions, {"core.idea"}, "", "es", None,
                                   "Project", "Ask.", "", agent_working=False)
        settings = tree(markup).find(**{"data-theme-settings": ""})
        self.assertIsNotNone(settings)
        text = settings.visible_text()
        for english in ("Agent settings", "Update app theme", "Saved themes",
                        "Reset theme", "Save"):
            self.assertNotIn(english, text)
        self.assertIn("Configuración del agente", text)
        self.assertIn("Guardar", text)
        self.assertIn('data-lang="es"', markup)

    def test_hero_metadata_keys_and_values_share_an_opposed_grid_edge(self) -> None:
        style_node = next(node for node in tree(self.markup()).all("style")
                          if "dh-article" in node.visible_text())
        style = style_node.visible_text()
        grid = declarations(style, ".dh-hero-meta")
        keys = declarations(style, ".dh-hero-meta .dh-label")
        values = declarations(style, ".dh-hero-meta .dh-value")
        self.assertIn("max-content minmax(0,1fr)", grid.get("grid-template-columns", ""))
        self.assertEqual(keys.get("text-align"), "right")
        self.assertEqual(keys.get("justify-self"), "end")
        self.assertEqual(values.get("text-align"), "left")
        self.assertEqual(values.get("justify-self"), "start")

    def test_live_status_keeps_emoji_out_of_the_wrapping_text_column(self) -> None:
        document = tree(self.markup("🎨 Redrawing the cover", True))
        status = document.find(**{"class": "dh-live"})
        icon = status.find(**{"class": "dh-live-icon"})
        detail = status.find(**{"class": "dh-live-detail"})
        copy = status.find(**{"class": "dh-live-copy"})
        self.assertEqual(icon.visible_text(), "🎨")
        self.assertEqual(detail.visible_text(), "Redrawing the cover")
        self.assertIs(icon.parent, status)
        self.assertIs(copy.parent, status)
        style_node = next(node for node in document.all("style")
                          if "dh-article" in node.visible_text())
        live = declarations(style_node.visible_text(), ".dh-live")
        self.assertRegex(live.get("grid-template-columns", ""), r"^\d+px minmax\(0,1fr\)$")


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

    def test_select_reset_and_save_preserve_the_safe_saved_themes(self) -> None:
        server = json.dumps(str(ROOT / "companion" / "server.cjs"))
        with tempfile.TemporaryDirectory() as tmp:
            source = (
                f"process.env.BRAINSTORM_PROJECT_DIR={json.dumps(tmp)};"
                f"const s=require({server});"
                "const safe={bg:'#111111',ink:'#ffffff',accent:'#73d2ff',font:'system-ui'};"
                "s.updateThemeSpec({action:'save',mode:'new',id:'one',name:'One',elements:safe});"
                "s.updateThemeSpec({action:'save',mode:'new',id:'two',name:'Two',elements:safe});"
                "s.updateThemeSpec({action:'select',id:'one'});"
                "s.updateThemeSpec({action:'follow',enabled:true});"
                "const x=s.updateThemeSpec({action:'reset'});"
                "if(x.selected!==null||x.followArtDirection!==false||x.themes.length!==2)process.exit(1);"
                "if(x.themes.some(t=>s.contrast(t.elements.bg,t.elements.ink)<4.5))process.exit(2);"
            )
            completed = subprocess.run(["node", "-e", source], capture_output=True,
                                       text=True)
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

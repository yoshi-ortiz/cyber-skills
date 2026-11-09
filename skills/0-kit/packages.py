#!/usr/bin/env python3
"""kit: install only the skills a project calls for, from the PACK.md catalog, or fail.

  packages.py                          verify: gate both scopes, install nothing
  packages.py kit-starter-pack         install the `core` domain globally; bare verify advises it on a first run
  packages.py <token>... [-g]          install into this project, or globally with -g.
                                       A token is a domain, a skill, owner/repo:skill, or owner/repo.
  packages.py add owner/repo [--skill a b]   add a catalog row; installs nothing
  packages.py remove <skill>... [-g]   uninstall from this project, or globally
  packages.py list [-g]                passed to `skills list`
  packages.py stamp                    write publisher metadata and a `publisher:` description prefix into every installed SKILL.md
  packages.py export <skill>... [-g]   zip skills for ChatGPT web upload, which has no scripted route
  --dry-run                            run every gate and print the installs; change nothing

Every check is a hard gate: one problem stops the run with exit code 1.

CLI reference: https://github.com/vercel-labs/skills/blob/main/docs/commands.md
Discovery rules: https://github.com/vercel-labs/skills/blob/main/docs/creating-skills.md
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CLI_VERSION = "1.7.4"  # npm `skills`, published 2026-10-19. Pin, never `latest`.
CLI = ["npx", "--yes", f"skills@{CLI_VERSION}"]
MAX_SKILLS = 40  # per session: global plus this project
MAX_LISTING_BYTES = 12000  # sum of descriptions: what every session pays to list them
TIMEOUT = 600  # seconds per command
SELF = "0-kit"  # installed from this package's own repo, not from a catalog row

HOME = Path.home()
PACK = Path(__file__).with_name("PACK.md")
CACHE = HOME / ".cache/kit"
INDEX = CACHE / "index.json"
ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")
if os.environ.get("KIT_TELEMETRY") != "1":
    ENV.update(DISABLE_TELEMETRY="1", DO_NOT_TRACK="1")  # also skips the CLI's audit requests

ROW = re.compile(
    r"^\s*[*-]\s+(?:<img[^>]*>\s*)?\[[^\]]+\]\(https://github\.com/([\w.-]+/[\w.-]+?)/?\)\s*(?::\s*(.*))?$"
)
BULLET = re.compile(r"^\s*[*-]\s")
NAME = re.compile(r"\[([^\]]+)\]\(https://github\.com/")
ITEM = re.compile(r"^\s*\d+\.\s+(\S+)")
REPO = re.compile(r"[\w.-]+/[\w.-]+")


def gate(problems, hint=""):
    if not problems:
        return
    print(f"\nFAIL: {len(problems)} problem(s)")
    for p in problems[:20]:
        print("  - " + p)
    if len(problems) > 20:
        print(f"  ... and {len(problems) - 20} more")
    if hint:
        print(hint)
    sys.exit(1)


def run(cmd, **kw):
    try:
        return subprocess.run(cmd, stdin=subprocess.DEVNULL, timeout=TIMEOUT, env=ENV, **kw)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", f"timed out after {TIMEOUT}s")


# PACK.md -----------------------------------------------------------------

class Pack:
    def __init__(self, text):
        self.text, self.rows, self.domains, self.agents, problems = text, {}, {}, [], []
        self.owned, self.publisher = set(), {}
        section = domain = ""
        for n, line in enumerate(text.splitlines(), 1):
            if line.startswith("# "):
                section, domain = line[2:].strip().lower(), ""
            elif line.startswith("## ") and section == "domains":
                domain = line[3:].strip().lower()
                if domain in self.domains:
                    problems.append(f"PACK.md:{n} repeats domain {domain}")
                self.domains[domain] = []
            elif section == "batteries included" and BULLET.match(line):
                m = ROW.match(line)
                if not m:
                    problems.append(f"PACK.md:{n} is not `* [Name](https://github.com/owner/repo): skills`")
                elif m.group(1).lower() in self.rows:
                    problems.append(f"PACK.md:{n} repeats {m.group(1)}")
                else:
                    names = [s for s in re.split(r"[,\s]+", m.group(2) or "") if s]
                    self.rows[m.group(1).lower()] = (m.group(1), names)
                    self.publisher[m.group(1).lower()] = NAME.search(line).group(1)
            elif section in ("agents", "agent-owned", "domains") and re.match(r"^\s*\d+\.", line):
                m = ITEM.match(line)
                if not m:
                    problems.append(f"PACK.md:{n} is an empty list item")
                elif section == "agents":
                    if m.group(1) == "*":
                        problems.append(f"PACK.md:{n} `*` links every agent, and some get copies. Name agents.")
                    self.agents.append(m.group(1))
                elif section == "agent-owned":
                    self.owned.add(m.group(1))
                elif not domain:
                    problems.append(f"PACK.md:{n} is a list item outside a `## domain`")
                else:
                    self.domains[domain].append(m.group(1))
        if not self.rows:
            problems.append("PACK.md has no rows under `# Batteries included`")
        if not self.agents:
            problems.append("PACK.md has no agents under `# Agents`")
        if "core" not in self.domains:
            problems.append("PACK.md has no `## core` domain; kit-starter-pack installs it")
        gate(problems)

    def repo(self, name):
        return self.rows.get(name.lower(), (None, None))[0]


# Sources -----------------------------------------------------------------

def frontmatter(path):
    lines = path.read_text(errors="ignore").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None, False
    fm = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm.append(line)
    name = desc = None
    for i, line in enumerate(fm):
        if line.startswith("name:"):
            name = line[5:].strip().strip("'\"")
        elif line.startswith("description:"):
            desc = line[12:].strip()
            if desc in ("", ">", "|", ">-", "|-"):
                desc = " ".join(x.strip() for x in fm[i + 1:] if x[:1] in (" ", "\t")).strip()
            desc = desc.strip("'\"")
    return name, desc, any(re.match(r"^\s+internal:\s*true\b", x) for x in fm)


def discover(root):
    """Approximates the CLI's discovery rules; the post-install gates catch any disagreement."""
    if (root / "SKILL.md").is_file():
        files = [root / "SKILL.md"]
    else:
        containers = [d for d in [root / "skills", *root.glob(".*/skills")] if d.is_dir()]
        files = [f for c in containers for f in c.rglob("SKILL.md") if len(f.relative_to(c).parts) <= 4]
        if not files:
            files = [f for f in root.rglob("SKILL.md") if not {".git", "node_modules"} & set(f.parts)]
    dirs, found = {f.parent for f in files}, {}
    for f in sorted(files, key=lambda f: len(f.parts)):
        if any(p in dirs for p in f.parent.parents):
            continue  # a shallower SKILL.md shadows this one
        name, desc, internal = frontmatter(f)
        if name and desc and not internal:
            found.setdefault(name, len(desc.encode()))
    return found


def index_one(repo, cached):
    url = f"https://github.com/{repo}.git"
    head = run(["git", "ls-remote", url, "HEAD"], capture_output=True, text=True)
    sha = head.stdout.split()[0] if head.returncode == 0 and head.stdout else None
    if not sha:
        return repo, None, f"{repo}: does not resolve at {url}"
    if cached.get("sha") == sha:
        return repo, cached, None
    dest = CACHE / repo.replace("/", "@")
    if (dest / ".git").is_dir():
        steps = [["git", "-C", str(dest), "fetch", "--depth", "1", "--quiet", "origin", "HEAD"],
                 ["git", "-C", str(dest), "reset", "--hard", "--quiet", "FETCH_HEAD"]]
    else:
        steps = [["git", "clone", "--depth", "1", "--quiet", url, str(dest)]]
    for step in steps:
        if run(step, capture_output=True).returncode:
            return repo, None, f"{repo}: does not clone from {url}"
    return repo, {"sha": sha, "skills": discover(dest)}, None


def index(pack, repos):
    CACHE.mkdir(parents=True, exist_ok=True)
    try:
        idx = json.loads(INDEX.read_text())
    except (FileNotFoundError, ValueError):
        idx = {}
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda r: index_one(r, idx.get(r, {})), repos))
    problems = [err for _, _, err in results if err]
    for repo, entry, _ in results:
        if entry:
            idx[repo] = entry
            offered = pack.rows[repo.lower()][1]
            problems += [f"{repo}: catalog offers {n}, which the repo does not have"
                         for n in offered if n not in entry["skills"]]
    INDEX.write_text(json.dumps(idx, indent=1, sort_keys=True))
    gate(problems)
    return {r: {n: b for n, b in idx[r]["skills"].items() if not pack.rows[r.lower()][1]
                or n in pack.rows[r.lower()][1]} for r in repos}


def resolve(pack, tokens):
    """Map tokens to {skill: (repo, description bytes)}."""
    items = []
    for t in tokens:
        items += pack.domains[t.lower()] if t.lower() in pack.domains else [t]
    needed = {pack.repo(i.split(":")[0]) for i in items if pack.repo(i.split(":")[0])}
    if any(not pack.repo(i.split(":")[0]) for i in items):
        needed = {repo for repo, _ in pack.rows.values()}  # a bare name: search the catalog
    offered = index(pack, sorted(needed))
    picks, problems = {}, []
    for item in items:
        repo_part, _, name = item.partition(":")
        repo = pack.repo(repo_part)
        if repo and name:
            hits = [repo] if name in offered[repo] else []
        elif repo:
            for n in offered[repo]:
                picks.setdefault(n, (repo, offered[repo][n]))
            continue
        elif REPO.fullmatch(item):
            problems.append(f"{item}: not in the catalog. Add it: packages.py add {item}")
            continue
        else:
            name = item
            hits = [r for r in offered if name in offered[r]]
        if not hits:
            problems.append(f"{item}: no catalog source offers this skill")
        elif len(hits) > 1:
            problems.append(f"{item}: offered by {', '.join(hits)}. Write it as owner/repo:{name}")
        elif name in picks and picks[name][0] != hits[0]:
            problems.append(f"{name}: picked from both {picks[name][0]} and {hits[0]}")
        else:
            picks[name] = (hits[0], offered[hits[0]][name])
    problems += [f"{n}: an agent already ships a skill named {n} (PACK.md # Agent-owned)" for n in picks if n in pack.owned]
    gate(problems)
    return picks


# Scopes ------------------------------------------------------------------

def prefix_description(fm, tag):
    """Prefix `description:` with `tag` in place: every agent lists it, and names cannot carry a colon."""
    d = next((k for k, x in enumerate(fm) if x.startswith("description:")), None)
    if d is None:
        return False
    val = fm[d][12:].strip()
    if val[:1] in (">", "|"):  # block scalar: a colon is safe in its content
        if d + 1 >= len(fm) or not fm[d + 1].strip():
            return False
        body = fm[d + 1].lstrip()
        if not body.startswith(tag + " "):
            fm[d + 1] = fm[d + 1][:len(fm[d + 1]) - len(body)] + tag + " " + body
    elif not val:
        return False  # plain multi-line scalar: a colon would break it
    elif val[0] in "'\"":
        if not val[1:].startswith(tag + " "):
            fm[d] = f"description: {val[0]}{tag} {val[1:]}"
    elif not val.startswith(tag + " "):
        fm[d] = "description: " + json.dumps(f"{tag} {val}")
    return True


def stamp(skill, want, write):
    """Put `want` in the SKILL.md frontmatter `metadata:` map (agentskills.io spec). ok, changed or cannot."""
    lines = skill.read_text().split("\n")
    try:
        end = lines.index("---", 1)
    except ValueError:
        return "cannot"
    fm = lines[1:end]
    i = next((k for k, x in enumerate(fm) if x.startswith("metadata:")), None)
    if i is None:
        fm.append("metadata:")
        i = len(fm) - 1
    elif fm[i].strip() != "metadata:":
        return "cannot"  # an inline map is not safely editable
    j = i + 1
    while j < len(fm) and fm[j][:1] in (" ", "\t"):
        j += 1
    block = fm[i + 1:j]
    for k, v in want.items():
        line = f"  {k}: {json.dumps(v)}"
        old = [x for x in block if x.split(":", 1)[0].strip() == k]
        if old != [line]:
            block = [x for x in block if x not in old] + [line]
    fm = fm[:i + 1] + block + fm[j:]
    if not prefix_description(fm, re.sub(r"[^a-z0-9]+", "-", want["publisher"].lower()).strip("-") + ":"):
        return "cannot"
    new = lines[:1] + fm + lines[end:]
    if new == lines:
        return "ok"
    if write:
        skill.write_text("\n".join(new))
    return "changed"


class Scope:
    def __init__(self, is_global):
        self.is_global = is_global
        if is_global:
            self.root, self.lock, self.name, self.tracked = HOME, HOME / ".agents/.skill-lock.json", "global", set()
        else:
            top = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
            if top.returncode:
                gate(["not inside a git project. Pass -g to install globally."])
            self.root = Path(top.stdout.strip())
            self.lock, self.name = self.root / "skills-lock.json", "project"
            files = run(["git", "-C", str(self.root), "ls-files"], capture_output=True, text=True).stdout
            self.tracked = {str(p) for f in files.splitlines() for p in [Path(f), *Path(f).parents]}
        self.store = self.root / ".agents/skills"

    def locked(self):
        try:
            return json.loads(self.lock.read_text()).get("skills", {})
        except FileNotFoundError:
            return {}

    def folders(self):
        found = [*self.root.glob(".*/skills"), *self.root.glob(".config/*/skills"), self.root / ".pi/agent/skills"]
        if not self.is_global:
            found += self.root.glob("*/skills")
        return [f for f in dict.fromkeys(found) if f.is_dir()]  # Python 3.14 globs match dot names with `*`

    def listing(self, names):
        return sum(len((frontmatter(self.store / n / "SKILL.md")[1] or "").encode())
                   for n in names if (self.store / n / "SKILL.md").is_file())

    def stamps(self, pack, write):
        """Every installed skill carries its catalog publisher. Write fixes; otherwise report."""
        bad = []
        for name, entry in self.locked().items():
            src, skill = entry.get("source", ""), self.store / name / "SKILL.md"
            if src.lower() not in pack.publisher or not skill.is_file():
                continue  # drift() reports these
            want = {"publisher": pack.publisher[src.lower()], "source": src, "source-url": f"https://github.com/{src}"}
            res = stamp(skill, want, write)
            if res == "cannot":
                bad.append(f"cannot stamp {skill}: inline `metadata:` or no frontmatter")
            elif res == "changed" and not write:
                bad.append(f"{self.name}: {name} has no publisher stamp. Run: python3 packages.py stamp")
        return bad

    def drift(self, pack):
        lock, problems = self.locked(), []
        for name, entry in lock.items():
            if name != SELF and not pack.repo(entry.get("source", "")):
                problems.append(f"{self.name}: {name} comes from {entry.get('source')}, not from the catalog")
            if not (self.store / name / "SKILL.md").is_file():
                problems.append(f"{self.name}: {name} is in the lock but not in {self.store}")
        for folder in self.folders():
            for p in sorted(folder.iterdir()):
                if p.name.startswith(".") or p.name in pack.owned or str(p.relative_to(self.root)) in self.tracked:
                    continue
                if p.name not in lock:
                    problems.append(f"foreign entry: {p}")
                elif folder != self.store and p.resolve() != (self.store / p.name).resolve():
                    problems.append(f"a copy, not a link: {p}")
                elif folder not in (self.store, self.root / ".claude/skills"):
                    problems.append(f"{p.name} is listed twice for the agents reading {folder}: it is already in {self.store}")
        return problems


def scopes():
    inside = run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).returncode == 0
    return [Scope(True)] + ([Scope(False)] if inside else [])


def twice():
    """A skill in both the global and the project store is listed twice in every session."""
    seen, problems = {}, []
    for s in scopes():
        for n in s.locked():
            if n in seen:
                problems.append(f"{n}: installed in {seen[n]} and {s.name}; each session lists it twice")
            seen[n] = s.name
    return problems


def budget(pack, extra=None):
    names, listing = set(), 0
    for s in scopes():
        names |= set(s.locked())
        listing += s.listing(s.locked())
    for n, (_, size) in (extra or {}).items():
        if n not in names:
            names.add(n)
            listing += size
    problems = []
    if len(names) > MAX_SKILLS:
        problems.append(f"{len(names)} skills per session, over the {MAX_SKILLS} cap")
    if listing > MAX_LISTING_BYTES:
        problems.append(f"{listing} description bytes per session, over the {MAX_LISTING_BYTES} cap")
    return problems, len(names), listing


# Commands ----------------------------------------------------------------

def install(pack, tokens, is_global, dry):
    scope = Scope(is_global)
    gate(scope.drift(pack), f"Clean {scope.root} first: every installed skill must come from the catalog.")
    picks = resolve(pack, tokens)
    lock = scope.locked()
    clash = [f"{n}: installed from {lock[n].get('source')}, picked from {repo}"
             for n, (repo, _) in picks.items() if n in lock and lock[n].get("source", "").lower() != repo.lower()]
    gate(clash)
    gate([f"{n}: already installed in {s.name}; each session would list it twice"
          for s in scopes() if s.is_global != is_global for n in picks if n in s.locked()])
    new = {n: v for n, v in picks.items() if n not in lock}
    problems, count, listing = budget(pack, new)
    gate(problems, "Install fewer skills, or remove some first.")
    by_repo = {}
    for n, (repo, _) in sorted(new.items()):
        by_repo.setdefault(repo, []).append(n)
    agents = [x for a in pack.agents for x in ("-a", a)]
    cmds = [CLI + ["add", repo, *(["-g"] if is_global else []), "-y", *agents, "--skill", *names]
            for repo, names in by_repo.items()]
    print(f"{scope.name}: {len(new)} new skill(s), {len(picks) - len(new)} already installed; "
          f"session after install: {count} skills, {listing} description bytes")
    for cmd in cmds:
        print("$ " + shlex.join(cmd))
    if dry or not cmds:
        print("dry run: nothing changed" if dry else "nothing to install")
        return 0
    if scope.lock.is_file():
        backup = CACHE / f"{scope.name}-lock-{time.strftime('%Y%m%d-%H%M%S')}.json"
        shutil.copy2(scope.lock, backup)
        print(f"lock backed up: {backup}")
    before = {p.name for p in scope.root.iterdir()}
    for cmd in cmds:
        if run(cmd, cwd=scope.root).returncode:
            gate([f"install failed: {shlex.join(cmd)}"], "Fix it and run again; installs are idempotent.")
    lock, problems = scope.locked(), scope.drift(pack)
    problems += [f"not in lock after install: {n}" for n in new if n not in lock]
    if not scope.is_global:
        problems += [f"install created {scope.root / p} in the project root"
                     for p in sorted({p.name for p in scope.root.iterdir()} - before)
                     if not p.startswith(".") and p != "skills-lock.json"]
    problems += scope.stamps(pack, True)
    problems += budget(pack)[0]
    gate(problems, "Installed, but not as declared. Lock backup is in ~/.cache/kit.")
    print(f"ok: {len(new)} installed into {scope.name}")
    return 0


def verify(pack):
    problems = [p for s in scopes() for p in s.drift(pack) + s.stamps(pack, False)] + twice()
    budget_problems, count, listing = budget(pack)
    gate(problems + budget_problems)
    print(f"ok: {count} skills per session, {listing} description bytes, all from the catalog")
    if not [n for s in scopes() for n in s.locked() if n != SELF]:
        print("first run: nothing is installed yet. Install the core skills everywhere: "
              "python3 packages.py kit-starter-pack")
    return 0


def remove(names, is_global, dry):
    scope = Scope(is_global)
    lock = scope.locked()
    gate([f"{n}: not installed in {scope.name}" for n in names if n not in lock] or
         ([] if names else ["name the skills to remove"]))
    cmd = CLI + ["remove", *(["-g"] if is_global else []), "-y", "--skill", *names]
    print("$ " + shlex.join(cmd))
    if dry:
        return 0
    gate([f"remove failed: {shlex.join(cmd)}"] if run(cmd, cwd=scope.root).returncode else [])
    gate([f"still installed: {n}" for n in names if n in scope.locked()])
    print(f"ok: removed {len(names)} from {scope.name}")
    return 0


def add_row(pack, rest):
    if not rest or not REPO.fullmatch(rest[0]) or (rest[1:] and rest[1] not in ("-s", "--skill")):
        sys.exit("usage: packages.py add owner/repo [--skill a b]")
    repo, names = rest[0], rest[2:]
    gate([f"already in the catalog: {repo}"] if pack.repo(repo) else [])
    row = f"* [{repo}](https://github.com/{repo})" + (": " + ", ".join(names) if names else "")
    lines = pack.text.splitlines()
    start = lines.index("# Batteries included")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("# ")), len(lines))
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, row)
    new = Pack("\n".join(lines) + "\n")
    index(new, [repo])  # gates: resolves, clones, offers only skills it has
    PACK.write_text(new.text)
    print(f"catalog row added: {row}")
    return 0


def export(pack, names, is_global):
    """Zip stamped skills for ChatGPT web, which only takes uploads. Modes are normalized to 644/755."""
    scope = Scope(is_global)
    gate([f"{n}: not installed in {scope.name}" for n in names if n not in scope.locked()] or
         ([] if names else ["name the skills to export"]))
    gate(scope.stamps(pack, False))
    for n in names:
        out = Path.cwd() / f"{n}.zip"
        with zipfile.ZipFile(out, "w") as z:
            for f in sorted((scope.store / n).rglob("*")):
                if f.is_file() and not f.is_symlink():
                    info = zipfile.ZipInfo(f"{n}/{f.relative_to(scope.store / n).as_posix()}", (2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = (0o755 if os.access(f, os.X_OK) else 0o644) << 16
                    z.writestr(info, f.read_bytes())
        print(f"wrote {out}. Upload: ChatGPT > Skills > Create > Upload from your computer")
    return 0


def main(argv):
    dry, is_global = "--dry-run" in argv, "-g" in argv or "--global" in argv
    argv = [a for a in argv if a not in ("--dry-run", "-g", "--global")]
    gate([f"{t} not found; kit does not install runtimes" for t in ("npx", "git") if not shutil.which(t)])
    pack = Pack(PACK.read_text())
    if not argv or argv == ["verify"]:
        return verify(pack)
    verb, rest = argv[0], argv[1:]
    if verb == "kit-starter-pack":
        return install(pack, ["core"], True, dry)
    if verb == "stamp":
        gate([p for s in scopes() for p in s.stamps(pack, True)])
        print("ok: every installed skill carries its publisher")
        return 0
    if verb == "export":
        return export(pack, rest, is_global)
    if verb == "add":
        return add_row(pack, rest)
    if verb in ("remove", "rm"):
        return remove(rest, is_global, dry)
    if verb in ("list", "ls"):
        return subprocess.call(CLI + ["list", *(["-g"] if is_global else []), *rest], env=ENV)
    return install(pack, argv, is_global, dry)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

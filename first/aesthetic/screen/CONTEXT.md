---
purpose: the CSS and JS the harness renders into the review screen
admits: .css and .js files loaded by `bootstrap_harness._screen`, one per emitted <style> or <script> block
refuses: companion files, harness logic, anything a project should own or edit
max_file_bytes: 50000
---

# Screen

`bootstrap_harness.py` emits a review article and a controls block. Both are
browser assets, and both used to be Python string literals — 1,447 lines of CSS
and JS that no editor highlighted, no formatter touched, and `node --check`
could not see. That is most of why the module sits at ten times its byte budget
(R-15).

`_screen(name)` reads a file here and wraps it in `<style>` or `<script>` by
extension. The wrapper is the only transform; the file is the emitted bytes.
Adding a block means adding a file here and one `_screen()` call there.

Not `companion/`: those files are vendored, a design run treats them as
read-only, and their contract refuses harness logic. These are harness-owned and
change with the harness.

`article.css` is 47 KB and is the reason the budget here is 50,000 rather than
the 40,000 next door. Splitting it is its own job, not a reason to keep it
inside Python.

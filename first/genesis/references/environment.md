---
type: Playbook
title: Reproducible development environment
description: Establish the runnable software environment required by the selected Item.
status: stable
---

# Reproducible development environment

Use this branch for software bootstrap or missing setup. A full environment
means every component needed to develop, run, verify and package this project;
its requirements determine whether it needs a database, UI, service or container.

1. **Inspect.** Read existing manifests, runtime constraints, setup instructions,
   configuration and CI. Identify what already works and what the selected Item
   lacks. Preserve the existing stack unless requirements justify a change.
   Done when each setup gap has an owner and a required capability.
2. **Scaffold.** Use maintained generators or native tooling with documentation
   matching the chosen versions. Add the applicable runtime manifest, dependency
   lockfile, source entry point, configuration example, ignore rules, development
   command, build/package command and verification command. Add local services,
   migrations and seed data only when the application requires them. Configuration
   examples contain placeholders; credentials come from the environment.
   Done when each required capability has an executable path, not a placeholder.
3. **Connect.** Wire a small real feature through the runtime and its required
   dependencies. Reuse the project's test runner and CI; when absent, provide
   automation for applicable build and verification checks. Document prerequisites,
   setup, run, test and package commands in the quickstart. Link their canonical
   definitions instead of copying configuration into agent instructions.
   Done when another developer can follow one coherent setup path.
4. **Verify.** Exercise the documented setup in a clean temporary checkout or
   equivalent isolated environment, launch the program and run a representative
   acceptance check plus the applicable build. Record versions, commands and
   results. If tools, credentials or access prevent a check, identify that exact
   gap and mark it unverified. Completion requires the runnable path to pass;
   generated files alone establish only that scaffolding exists.

---
type: Contract
title: Manifest and agent contract
description: Bootstrap and build completion rules for a tidy stack-native repository.
status: stable
---

# Manifest first

1. Inventory tracked and untracked files, manifests, lockfiles, workspace roots,
   generated outputs and existing setup commands. Identify the stack and each
   package owner from evidence. On a populated repo, preserve its working layout
   and map any required moves with their callers before changing paths.
   Done when existing work and the required setup gaps are accounted for.
2. Fetch or write the stack-native manifest before installing tools or generating
   application files. Use `package.json` for Node; preserve the chosen Python
   convention (`pyproject.toml`, or `requirements.txt` for dependency-only setup);
   use the equivalent native manifest for other stacks. A requirements file alone
   does not define a distributable Python package. Declare runtime constraints,
   direct dependencies and development tools in their owning manifest; retain
   the package manager's appropriate lock or reproducibility mechanism.
   Done when setup has one authoritative dependency source per package.
3. Write `docs/AGENT_CONTRACT.md` and link it from `AGENTS.md`, plus `CLAUDE.md`
   when present. Reuse an existing equivalent contract. Address the project's
   applicable LLM failure modes with executable checks: version/API guessing,
   invented commands, arithmetic or parsing, context drift, dependency omissions,
   misplaced artifacts, secret handling and unsupported completion claims.
   For each record **trigger, authoritative source, action, check, failure path**.
   Source commands and versions from manifests, tooling help and version-matched
   documentation; fetch missing facts and update the manifest before use. Keep
   facts in their source; the agent contract holds pointers and obligations.
   Done when each applicable failure mode has a check or a named missing tool.
4. Include a cleanliness contract: stack-native source/test/config placement,
   package boundaries and exports, runtime versus development dependencies,
   ignored caches and build outputs, placeholder-only environment examples,
   and a single documented install/run/check/package path. Reconcile scaffold
   collisions with existing ownership. Remove only generated or scoped obsolete
   artifacts whose ownership and references have been verified; report unrelated
   cleanup separately. Done when every new or moved file has a stack-defined role.
5. Run the manifest-defined setup and applicable validation and package commands
   in an isolated environment. Inspect the resulting package for required files,
   unintended caches, local records and credentials. Verify entry points and
   imports from the artifact when the stack produces one. Recheck the diff and
   working tree for scaffold leftovers and accidental changes.
   Done when one invocation leaves a runnable, tidy project with passing evidence,
   or reports the exact blocker and incomplete criteria. Single shot is the
   delivery target; preserve measured failures and actual acceptance separately.

Build reuses these rules for changed packages and updates the contract when
ownership or commands change. A documentation-only package uses its own manifest
and publication checks; choose artifacts from the actual stack.

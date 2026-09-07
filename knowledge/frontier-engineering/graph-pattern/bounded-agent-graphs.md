---
type: Reference
title: Bounded agent graphs
description: Use stateful graph orchestration to make a multi-step workflow inspectable and pausable.
status: stable
resource: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
tags:
  - agent-graphs
  - langgraph
  - google-adk
generated:
  by: codex/gpt-5
  at: 2026-09-06T00:00:00-06:00
sources:
  - resource: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
    title: Thinking in LangGraph
    author: LangChain
  - resource: https://adk.dev/2.0/
    title: Agent Development Kit 2.0
    author: Google
---

# Bounded agent graphs

LangGraph describes a workflow as discrete nodes, transitions, and shared state.
Its examples keep raw state between nodes, format context on demand, route on
explicit decisions, and use interrupts for human review. The ADK 2.0 material
likewise presents agents, tools, and functions as graph nodes with routing,
state, events, evaluation, retries, and human-in-the-loop pauses.

## Purpose

Use a graph to make a multi-step workflow explicit:

```text
propose -> build -> observe -> evaluate -> accept/reject -> retain evidence
```

Each node should have declared inputs, outputs, allowed effects, and failure
exit. Persist only the evidence needed to resume or audit the run. Put an
approval or review pause before an irreversible external action or adoption.

## Boundary

Nodes, edges, checkpoints, retries, and state persistence make execution more
inspectable. They do not establish a correct objective, independent evaluation,
causal improvement, or permission to perform an external action. Those need an
evidence policy, evaluation design, rollback policy, and human authority outside
the graph engine.

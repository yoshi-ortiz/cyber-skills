---
type: Specification
title: Open Knowledge Format 0.2
description: The frontmatter, directory, and conformance rules a knowledge bundle must satisfy.
status: stable
resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
generated:
  by: claude/opus-5
  at: 2026-08-23T12:20:00-05:00
sources:
  - resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
    title: Open Knowledge Format, SPEC.md
    author: GoogleCloudPlatform/knowledge-catalog
---

# Open Knowledge Format 0.2

Cached so the skill never refetches it. This is the subset a knowledge bundle
uses; the linked spec is authoritative for anything not here.

## Frontmatter

One field is required. Everything else is recommended or optional, and a
consumer must not reject a bundle for a missing optional field, an unknown
`type`, or an extra key it does not recognise.

| Field | Status | Meaning |
| --- | --- | --- |
| `type` | **required** | Short string naming the kind of concept. Free text: `Reference`, `Playbook`, `Metric`, `BigQuery Table`. Non-empty. |
| `title` | recommended | Human-readable display name |
| `description` | recommended | Single sentence |
| `resource` | recommended | URI identifying the underlying asset |
| `tags` | recommended | YAML list of categorisation strings |

## Trust and provenance

| Field | Shape |
| --- | --- |
| `generated` | `{ by: <actor>, at: <timestamp> }`. Who produced the content, when. |
| `verified` | List of `{ by: <actor>, at: <timestamp> }` events |
| `sources` | List of materials it derives from. `resource` required; `id`, `title`, `author`, `usage_count`, `last_modified` optional. |
| `usage_window` | `{ from: <timestamp>, to: <timestamp> }`, framing `usage_count` |

**Actors** follow one convention: a tool is `<producer>/<version>`
(`claude/opus-5`), a person is `human:<id>`, a scheduled job is
`process:<id>`.

## Lifecycle

| Field | Values |
| --- | --- |
| `status` | `draft`, `stable`, `deprecated`. Defaults to `stable`. |
| `stale_after` | ISO 8601 timestamp after which the content is presumed stale |

## Attested computation

Type-specific and optional. A concept that is executable rather than
descriptive declares `runtime` (`bigquery`, `dbt`, `python`), `parameters` as
`{ name, type, required }` entries, `computation` as a path to the file,
`executor` as `{ resource, receipt }`, and `attester` as `{ resource }`.
Most knowledge files never need any of it.

## Reserved filenames

| File | Meaning |
| --- | --- |
| `index.md` | Directory listing, the entry point for progressive disclosure |
| `log.md` | Chronological update history, grouped by date, newest first |
| `references/` | Conventionally mirrors external material and code |

Reserved files are exempt from the frontmatter requirement.

## Conformance

A bundle conforms when every non-reserved `.md` file has parseable YAML
frontmatter, every one of those blocks carries a non-empty `type`, and any
`index.md` or `log.md` present follows the structure above. `okf.py check`
tests exactly that, plus index completeness, which is a bundle-level habit
rather than a spec rule.

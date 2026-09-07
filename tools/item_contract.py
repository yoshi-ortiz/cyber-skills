"""Load and validate one reviewed Compass Item contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def item_contract(root: Path, row: dict) -> tuple[dict, list[str]]:
    """Read the reviewed contract referenced by the roadmap; never infer criteria."""
    path = (root / row['contract']).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('contract path escapes project root')
    if not path.exists():
        return {'contract_ref': row['contract']}, [f"contract required: {row['contract']}"]
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('unsupported Item contract version')
    if data.get('item_id') != row['id']:
        raise ValueError('contract item_id mismatch')
    fields = ('acceptance_criteria', 'exclusions', 'read_paths', 'write_paths', 'proof_requirements')
    allowed = {'version', 'item_id', 'review_ref', 'budget_tokens', *fields}
    if set(data) - allowed:
        raise ValueError('unknown Item contract fields: ' + ', '.join(sorted(set(data) - allowed)))
    reasons = []
    for key in fields:
        value = data.get(key)
        if value is None:
            reasons.append(f'{key} required')
        elif not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
            raise ValueError(f'{key}: expected nonempty strings')
        elif not value and key in {'acceptance_criteria', 'proof_requirements'}:
            reasons.append(f'{key} required')
        if key in {'read_paths', 'write_paths', 'proof_requirements'} and isinstance(value, list):
            for entry in value:
                if Path(entry).is_absolute() or '..' in Path(entry).parts or not (root / entry).resolve().is_relative_to(root.resolve()):
                    raise ValueError(f'{key}: path escapes project root')
    if not isinstance(data.get('review_ref'), str) or not data['review_ref'].strip():
        reasons.append('review_ref required')
    budget = data.get('budget_tokens')
    if 'budget_tokens' not in data:
        reasons.append('budget_tokens required (null explicitly means uncapped)')
    elif budget is not None and (type(budget) is not int or budget < 0):
        raise ValueError('budget_tokens: expected nonnegative integer or null')
    return {**{key: data.get(key) for key in (*fields, 'budget_tokens', 'review_ref')},
            'contract_ref': row['contract'], 'contract_revision': hashlib.sha256(raw).hexdigest()}, reasons

---
purpose: repository context indexing and advisory corpus exploration
admits: the indexing script and its tests
refuses: doctrine, and any import from another skill's scripts
max_file_bytes: 30000
---

# Scripts

`ontology.py` owns repository manifests, local embedding, transactional pgvector
indexing, exact retrieval and EVoC exploration manifests. Optional dependencies
are imported only by the commands that need them.

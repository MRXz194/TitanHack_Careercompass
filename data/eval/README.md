# MI-02 skill extraction gold set

`skills_gold.jsonl` is produced by M2 and reviewed by M3. It must contain exactly
100 unique postings, at least three regions and at least five career groups. Do not
copy crawler-provided tags into `skills`: those tags are predictions, not gold.

Each line contains labels only, so the repository does not republish job descriptions:

```json
{"posting_id":"source_123","region":"hanoi","career_group":"software","skills":["Python","SQL"]}
```

Rules:

- Freeze the selected posting IDs before dictionary/LLM tuning.
- M2 labels against taxonomy version `1.0.0`, hash
  `sha256:67c18ff3a8bd14f71d29e0c3de27f7035fb387e6aa797c5c39ecccd9fd961e2a`;
  use canonical names only.
- Empty `skills` is valid when a posting contains no concrete skill.
- Keep the source snapshot ID/hash separately in the D-05 handoff and evaluation report.
- Do not commit descriptions, company names, applicant data, or restricted source content.

Run after M3 has generated `postings_enriched.jsonl` from the same snapshot:

```bash
python data/pipeline/evaluate_skill_extraction.py
```

Until the 100 records are independently labeled and handed off, extraction precision,
recall and F1 remain `NOT_RUN`.

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

## MI-03 career mapping evaluation

`career_mapping_gold.jsonl` is a separate, independently reviewed sample of exactly
50 unique postings from the same D-05 snapshot used by the mapper. Keep labels out of
rule tuning until the baseline is frozen. Each line contains only evaluation metadata:

```json
{"posting_id":"source_123","source":"source-name","region":"hanoi","career_id":"ke-toan"}
```

`career_id` must be a D-07 KB ID or `unmapped`. Do not commit descriptions, company
names or applicant data. Report exact-match accuracy with denominator 50 plus mapped
coverage by source and region. The 10-record fictional fixture is wiring evidence only;
it must never be reported as the MI-03 accuracy metric.

Until D-05, D-07 and the 50 independent labels are handed off, career mapping accuracy
remains `NOT_RUN`. The `career-mapping-v1-stub` output is explicitly provisional and
must not be used to claim the ≥85% fallback threshold.

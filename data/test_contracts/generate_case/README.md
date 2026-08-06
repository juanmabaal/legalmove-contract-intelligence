# Generate Case

This test case was generated to validate the full LegalMove Contract Intelligence pipeline using a synthetic consulting services agreement and its amendment.

The purpose of this case is to test whether the system can process generated contract images, extract their text through a vision model, build a structural contextual map, and identify final legal changes through the ExtractionAgent.

---

## Files

```text
original_contract.png
amendment.png
```

---

## Case Type

```text
Generated contract-amendment pair
```

---

## Scenario

The original document is a consulting services agreement between:

```text
GreenAxis Energy LLC
Rivera Strategic Advisory S.A.S.
```

The amendment modifies several commercial and operational terms of the original agreement and introduces a new intellectual property clause.

---

## Original Contract Summary

The original contract includes the following sections:

```text
1. Alcance del Servicio
2. Duración
3. Honorarios
4. Entregables
5. Confidencialidad
6. Legislación Aplicable
```

### Original Key Terms

```text
Service scope:
Strategic consulting services related to renewable energy project expansion.

Duration:
6 months from the signing date.

Fees:
USD 8,000 monthly fee.

Deliverables:
Monthly progress reports and a final report with strategic recommendations.

Confidentiality:
All exchanged project information is considered confidential.

Governing law:
Laws of the State of California.
```

---

## Amendment Summary

The amendment includes the following sections:

```text
1. Alcance del Servicio
2. Duración
3. Honorarios
4. Entregables
5. Confidencialidad
6. Legislación Aplicable
7. Propiedad Intelectual
```

### Amendment Key Terms

```text
Service scope:
Strategic consulting services related to renewable energy project expansion and regulatory analysis.

Duration:
9 months from the signing date.

Fees:
USD 9,500 monthly fee.

Deliverables:
Biweekly progress reports and a final report with strategic recommendations.

Confidentiality:
No substantive change.

Governing law:
No substantive change.

Intellectual Property:
All deliverables produced during the project become property of the Client once final payment is made.
```

---

## Expected Structural Changes

The ContextualizationAgent should identify the following structural relationships:

```text
Section 1 → appears structurally modified
Section 2 → appears structurally modified
Section 3 → appears structurally modified
Section 4 → appears structurally modified
Section 5 → same or equivalent
Section 6 → same or equivalent
Section 7 → new in amendment
```

---

## Expected Extracted Changes

### Modifications

```text
1. Alcance del Servicio
The amendment expands the scope of services by adding regulatory analysis.

2. Duración
The service duration changes from 6 months to 9 months.

3. Honorarios
The monthly fee changes from USD 8,000 to USD 9,500.

4. Entregables
The progress report frequency changes from monthly to biweekly.
```

### Additions

```text
7. Propiedad Intelectual
The amendment adds a new intellectual property clause stating that all deliverables produced during the project become property of the Client once final payment is made.
```

### Deletions

```text
None expected.
```

---

## Expected Topics Touched

```text
Servicios de Consultoría
Duración del Contrato
Honorarios
Entregables
Propiedad Intelectual
```

---

## Expected Pipeline

```text
1. Parse original contract image
2. Parse amendment image
3. Build contextual structural map
4. Extract final legal changes
5. Validate final JSON with Pydantic
6. Save structured output under outputs/examples
```

---

## Test Command

Run this command from the project root:

```bash
uv run python -m src.main --original data/test_contracts/generate_case/original_contract.png --amendment data/test_contracts/generate_case/amendment.png --case-id generate_case --vision-provider openai --llm-provider openai --pipeline extraction --save-output
```

---

## Expected Output File

```text
outputs/examples/generate_case_extraction_output.json
```

---

## Validation Criteria

The generated JSON should include:

```text
case_id = generate_case

original_contract:
- Parsed text from original_contract.png
- Provider metadata
- Model metadata
- Token usage
- Latency

amendment:
- Parsed text from amendment.png
- Provider metadata
- Model metadata
- Token usage
- Latency

contextualization:
- Original sections
- Amendment sections
- Section correspondences
- New blocks in amendment
- Structural summary
- Confidence score

extraction:
- sections_changed
- topics_touched
- additions
- deletions
- modifications
- unclear_items
- summary_of_the_change
- confidence_score
```

---

## Expected High-Level Result

The pipeline should identify that the amendment:

```text
- Expands the service scope.
- Extends the duration.
- Increases the monthly fee.
- Changes the deliverable frequency.
- Adds an intellectual property clause.
```

---

## Notes

This case is synthetic and intended for development, testing, demonstration, and evaluation purposes only.

It should not be treated as a real legal document or used as legal advice.
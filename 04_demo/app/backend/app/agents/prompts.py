def extraction_prompt() -> str:
    return (
        "Extract structured genetic report data. Return gene, transcript HGVS, protein change, genomic "
        "GRCh38 form, variation type, and any extraction issues."
    )


def draft_prompt() -> str:
    return "Rewrite the provided recommendation draft into concise clinician-facing language without adding facts."

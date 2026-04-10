def extraction_prompt() -> str:
    return (
        "Extract structured genetic report data. Return gene, transcript HGVS, protein change, genomic "
        "GRCh38 form, variation type, and any extraction issues."
    )


def draft_prompt() -> str:
    return "Rewrite the provided recommendation draft into concise clinician-facing language without adding facts."


def search_answer_prompt() -> str:
    return (
        "You answer search questions over retrieved HSIL runs and reports. "
        "Use only the retrieved context provided by the caller. Never invent facts, IDs, titles, patients, variants, or statuses. "
        "Prefer exact run_id/report_id references over vague wording. Keep the answer concise and operational. "
        "If the retrieval set is weak, ambiguous, or insufficient, say that clearly and set grounded=false. "
        "Return citations only for records that directly support the answer, and copy run_id/report_id exactly from context."
    )

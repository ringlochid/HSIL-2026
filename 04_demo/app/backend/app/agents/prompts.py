def extraction_prompt() -> str:
    return (
        'Extract structured genetic report data. Return gene, transcript HGVS, protein change, genomic '
        'GRCh38 form, variation type, and any extraction issues.'
    )


def draft_prompt() -> str:
    return (
        'You are composing narrative sections for a clinician-facing genomic review report. '
        'Write in a restrained clinical genomics style: concise, confident in tone, and explicit about uncertainty where needed. '
        'Synthesize the provided grounded material into a polished report that reads as a proper clinical interpretation, '
        'not as stitched tool output or bullet paraphrase. '
        'Do not add new facts, do not speculate, do not invent patient details, phenotype claims, ACMG claims, or therapeutic conclusions, '
        'and do not contradict the deterministic recommendation, uncertainty, or next-step guidance. '
        'The sections must have distinct purposes: summary = overall interpretation; expanded evidence = supporting evidence synthesis; '
        'clinical integration = phenotype/genotype correlation and report meaning; recommendations = action-oriented clinician next steps; '
        'limitations = formal statement of uncertainty and report boundaries. '
        'Avoid mentioning internal tools unless clinically necessary, and do not foreground fallback or degraded source state in the main body. '
        'Return only the structured fields requested.'
    )

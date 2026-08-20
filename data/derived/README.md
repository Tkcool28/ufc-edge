# Derived Data

Reserved for reproducible non-feature data products built from canonical data.

Examples may include compact identity crosswalk exports, coverage summaries, or operational snapshots that are useful to pipelines and QA but are not predictive feature definitions.

Rules:

- every file must be reproducible from canonical data + versioned code;
- no hand-edited truth lives here;
- no provider-specific raw payload belongs here;
- no predictive feature definition is hidden here;
- generated outputs must identify the canonical input/version that produced them.

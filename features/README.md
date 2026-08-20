# Features

Reserved for the later feature-design phase.

The current data phase may document whether raw/canonical fields can support a future feature family, but it must not freeze predictive feature formulas here yet.

When this phase opens, feature definitions/builders will consume only canonical data contracts and must remain leakage-safe. Models may choose among shared features, but may not silently redefine a shared field or feature for their own convenience.

The feature phase starts only after the data acquisition/canonicalization completion gate is explicitly closed.

from __future__ import annotations

import unittest
import numpy as np
import pandas as pd

from ufc_edge.models.m0 import (
    IDENTITY_COLUMNS,
    MATERIALIZED_COLUMNS,
    M0Logistic,
    PAIR_SPECS,
    empirical_experience_probability,
    fold_frames,
    history_depth_slice,
    metric_bundle,
    primary_population,
    swap_pair_columns,
    validate_model_columns_against_schema,
    M0Error,
)


def fixture(rows: int = 12) -> pd.DataFrame:
    dates=pd.date_range("2014-01-01",periods=rows,freq="180D")
    data={
        "fight_id":[f"f{i}" for i in range(rows)],
        "event_id":[f"e{i}" for i in range(rows)],
        "event_date":dates,
        "promotion":["UFC"]*rows,
        "binary_winner_eligible":[True]*rows,
        "fighter_1_win":[bool(i%2) for i in range(rows)],
        "scheduled_rounds":[3]*rows,
        "ctx__title_bout":[False]*rows,
        "ctx__weight_class":["Lightweight"]*rows,
    }
    for j,(_,a,b) in enumerate(PAIR_SPECS):
        data[a]=[float(i+j) for i in range(rows)]
        data[b]=[float(rows-i+j) for i in range(rows)]
    return pd.DataFrame(data)


class M0Tests(unittest.TestCase):
    def test_ufc_binary_filter(self):
        frame=fixture(6)
        frame.loc[0,"promotion"]="Bellator MMA"
        frame.loc[1,"binary_winner_eligible"]=False
        frame.loc[2,"event_date"]=pd.Timestamp("2009-12-31")
        out=primary_population(frame)
        self.assertNotIn("f0",set(out.fight_id))
        self.assertNotIn("f1",set(out.fight_id))
        self.assertNotIn("f2",set(out.fight_id))


    def test_f02_predictor_metadata_selection(self):
        schema={"columns":[{"name":c,"predictor":True} for c in MATERIALIZED_COLUMNS]}
        validate_model_columns_against_schema(schema)
        schema["columns"][0]["predictor"]=False
        with self.assertRaises(M0Error):
            validate_model_columns_against_schema(schema)

    def test_identity_columns_never_model_inputs(self):
        self.assertFalse(set(MATERIALIZED_COLUMNS)&IDENTITY_COLUMNS)
        self.assertFalse(any("fighter_1_id" in c or "fighter_2_id" in c for c in MATERIALIZED_COLUMNS))

    def test_no_sportsbook_fields(self):
        joined=" ".join(MATERIALIZED_COLUMNS).lower()
        for token in ("odds","sportsbook","roi","closing_line","price"):
            self.assertNotIn(token,joined)

    def test_chronological_folds_no_overlap(self):
        frame=fixture(24)
        frame["event_date"]=pd.date_range("2010-01-01",periods=24,freq="180D")
        pop=primary_population(frame)
        train,valid=fold_frames(pop,2015)
        self.assertLess(train.event_date.max(),valid.event_date.min())
        self.assertFalse(set(train.fight_id)&set(valid.fight_id))

    def test_empirical_orientation(self):
        train=fixture(10)
        valid=fixture(4)
        p=empirical_experience_probability(train,valid)
        swapped=swap_pair_columns(valid)
        q=empirical_experience_probability(train,swapped)
        np.testing.assert_allclose(p+q,1.0,atol=1e-12)

    def test_logistic_is_deterministic_and_swap_invariant(self):
        frame=fixture(20)
        frame.loc[3,PAIR_SPECS[1][1]]=np.nan
        target=frame["fighter_1_win"].astype(int)
        a=M0Logistic.fit(frame,target)
        b=M0Logistic.fit(frame,target)
        pa=a.predict_proba(frame)
        pb=b.predict_proba(frame)
        np.testing.assert_allclose(pa,pb,atol=1e-12)
        ps=a.predict_proba(swap_pair_columns(frame))
        np.testing.assert_allclose(pa+ps,1.0,atol=1e-10)

    def test_training_only_preprocessing(self):
        train=fixture(10)
        valid=fixture(2)
        col=PAIR_SPECS[1][1]
        train[col]=20.0
        valid[col]=9999.0
        model=M0Logistic.fit(train,train["fighter_1_win"].astype(int))
        self.assertNotEqual(model.projector.medians[PAIR_SPECS[1][0]],9999.0)

    def test_draw_nc_exclusion(self):
        frame=fixture(4)
        frame.loc[0,"binary_winner_eligible"]=False
        frame.loc[0,"fighter_1_win"]=None
        out=primary_population(frame)
        self.assertEqual(len(out),3)

    def test_metric_correctness(self):
        got=metric_bundle([0,1],[0.25,0.75])
        self.assertAlmostEqual(got["brier"],0.0625,places=12)
        self.assertAlmostEqual(got["accuracy"],1.0,places=12)

    def test_history_depth_terms_are_conservative(self):
        frame=fixture(3)
        a,b=PAIR_SPECS[0][1],PAIR_SPECS[0][2]
        frame.loc[0,[a,b]]=[0,5]
        frame.loc[1,[a,b]]=[1,2]
        frame.loc[2,[a,b]]=[3,4]
        self.assertEqual(history_depth_slice(frame).tolist(),["zero_history","sparse_history","established_history"])


if __name__=="__main__":
    unittest.main()

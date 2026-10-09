"""Coarse CTMC. Rates are per minute; GA/GB are actor-oriented, not positions."""
import numpy as np
from scipy.linalg import expm

def generator(entry, back, ground_ko, submission, standing_ko):
    values = np.r_[entry, back, ground_ko, submission, standing_ko]
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Invalid transition hazard')
    q = np.zeros((5, 5))
    q[0, 1:3] = entry
    q[0, 3] = standing_ko
    for i in range(2):
        q[i+1, 0] = back[i]
        q[i+1, 3] = ground_ko[i]
        q[i+1, 4] = submission[i]
    q[np.diag_indices(5)] = -q.sum(axis=1)
    return q

def transition(q, minutes=5.):
    if q.shape != (5, 5) or not np.isfinite(q).all():
        raise ValueError('Invalid generator')
    off = q.copy(); np.fill_diagonal(off, 0.)
    if (off < 0).any() or not np.allclose(q.sum(axis=1), 0., atol=1e-12):
        raise ValueError('Invalid generator rows')
    if not np.isfinite(minutes) or minutes <= 0:
        raise ValueError('Invalid time')
    p = expm(q*minutes)
    if not np.isfinite(p).all() or p.min() < -1e-12 or p.max() > 1+1e-12 or not np.allclose(p.sum(axis=1),1,atol=1e-12):
        raise ValueError('Invalid transition probabilities')
    # Only remove machine-roundoff, never repair an invalid transition.
    p = np.clip(p, 0., 1.)
    return p / p.sum(axis=1)[:, None]

def propagate(q, rounds, step_minutes=5.):
    if rounds not in (3, 5) or abs(5/step_minutes-round(5/step_minutes)) > 1e-10:
        raise ValueError('Unsupported round structure')
    p = transition(q, step_minutes)
    v = np.array([1.,0.,0.,0.,0.])
    for _ in range(rounds):
        for _ in range(round(5/step_minutes)):
            v = v@p
        v[0] = v[:3].sum(); v[1:3] = 0.
    result = np.array([v[3],v[4],v[0]])
    if not np.allclose(result.sum(),1.,atol=1e-12) or (result < 0).any():
        raise ValueError('Invalid terminal probabilities')
    if result[:2].sum() <= 0:
        raise ValueError('Undefined conditional finish probability')
    return result

def compose(raw, finish):
    if not np.isfinite(finish) or not 0 <= finish <= 1:
        raise ValueError('Invalid external MOV0 probability')
    k = raw[0]/raw[:2].sum()
    return k, np.array([finish*k, finish*(1-k), 1-finish])

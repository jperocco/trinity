"""Joint normalization/weight fitting with within-report ranking constraints."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import spearmanr

from fit_original_trinity import FEATURES


def raw_matrix(rows):
    return np.array([[r['target_share']/100, r['yprr'], r['air_yard_share']/100, r['redzone_targets']/r['games']] for r in rows])


def project(x, parameters):
    scales = np.exp(parameters[:4])
    coefficients = np.exp(parameters[4:8])
    powers = np.exp(parameters[8:12])
    normalized = (x/(x+scales))**powers
    return 10*(-np.expm1(-(normalized@coefficients)))


def dominance_conflicts(rows, tolerance=.005):
    x = raw_matrix(rows)
    conflicts = []
    for i in range(len(rows)):
        for j in range(len(rows)):
            if i != j and np.all(x[i] >= x[j]-1e-12) and np.any(x[i] > x[j]+1e-12) and rows[i]['score'] < rows[j]['score']-tolerance:
                conflicts.append({'dominant': rows[i]['player'], 'dominated': rows[j]['player'], 'score_gap': rows[j]['score']-rows[i]['score']})
    return conflicts


def fit(groups, ranking, seed):
    lower = np.log([.03,.3,.03,.1]+[.001]*4+[.25]*4)
    upper = np.log([.8,10.,1.5,10.]+[10.]*4+[4.]*4)
    initial = np.log([.25,2.,.35,1.]+[1.]*4+[1.]*4)
    rng = np.random.default_rng(seed)
    def residual(parameters):
        out = []
        for x,y in groups:
            p = project(x, parameters)
            # Reports weighted equally; no cross-report ranking comparisons.
            out.extend((p-y)/np.sqrt(len(y)))
            if ranking:
                pairs = [(i,j) for i in range(len(y)) for j in range(len(y)) if y[i] > y[j]+.005]
                if pairs:
                    out.extend([np.sqrt(.5/len(pairs))*max(0.,min(.2,y[i]-y[j])-(p[i]-p[j])) for i,j in pairs])
        return np.array(out)
    best = None
    for k in range(12):
        start = initial if k == 0 else np.clip(initial+rng.normal(0,.8,12),lower+.001,upper-.001)
        result = least_squares(residual,start,bounds=(lower,upper),max_nfev=500)
        objective = float(np.square(residual(result.x)).sum())
        if best is None or objective < best[0]: best=(objective,result.x)
    return best[1]


def metrics(x,y,parameters):
    p=project(x,parameters)
    pairs=[(i,j) for i in range(len(y)) for j in range(len(y)) if y[i]>y[j]+.005]
    return dict(mae=float(np.abs(p-y).mean()),max_error=float(np.abs(p-y).max()),spearman=float(spearmanr(y,p).statistic),
        ordered_pairs_correct=float(np.mean([p[i]>p[j] for i,j in pairs])))


def main():
    paths={'top12':'top12_week4.json','middle22':'middle22_new_capture.json'}
    rows={k:json.loads(Path('data/research/trinity_reference',p).read_text()) for k,p in paths.items()}
    groups={k:(raw_matrix(r),np.array([v['score'] for v in r])) for k,r in rows.items()}
    results={}
    for ranking in [False,True]:
        name='score_and_order' if ranking else 'score_only'
        parameters=fit(list(groups.values()),ranking,20261010)
        results[name]=dict(parameters=parameters.tolist(),scales=dict(zip(FEATURES,np.exp(parameters[:4]).tolist())),
            powers=dict(zip(FEATURES,np.exp(parameters[8:12]).tolist())),coefficients=dict(zip(FEATURES,np.exp(parameters[4:8]).tolist())),
            normalized_component_weights=dict(zip(FEATURES,(np.exp(parameters[4:8])/np.exp(parameters[4:8]).sum()).tolist())),
            reports={k:metrics(x,y,parameters) for k,(x,y) in groups.items()})
    transfers={}
    for origin,(x,y) in groups.items():
        parameters=fit([(x,y)],True,20261010)
        transfers[origin]={k:metrics(tx,ty,parameters) for k,(tx,ty) in groups.items() if k!=origin}
    conflicts={k:dominance_conflicts(r) for k,r in rows.items()}
    report=dict(method='Shared zero-anchored monotonic 0–10 formula; four feature weights, four normalization scales and four powers optimized jointly. 12 deterministic starts per fit; score-only versus score-plus-within-report-order objective. Reports equally weighted, kept as separate snapshots; no cross-report pair comparisons. Reciprocal transfer diagnostics fit one report and evaluate the other. They are not independent untouched validation.',
        formula='10*(1-exp(-sum(c_j*(x_j/(x_j+s_j))**p_j)))',results=results,transfer=transfers,
        dominance_conflicts=conflicts,
        limitations=['34 selected rows, potentially different cutoffs, no full-universe or low-score reference.',
            '12 fitted parameters are flexible relative to sample size; reciprocal transfer and dominance audit are essential. No claim of recovered original weights.',
            'Reported weights depend on feature scales and powers; not directly comparable to earlier fixed-scale weights.',
            'Displayed rounding can affect dominance; selected conflicts should be checked against visible values.',
            'Same inputs can omit proprietary components, position normalization, thresholds or other transformations. Dominance violations rule out this monotonic four-feature family, not every possible original model.',
            'No individual overrides, JJ/FP source joins, model promotion or panel changes.'])
    Path('docs/TRINITY_NORMALIZATION_TEST.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    lines=['# Trinity: pesos e normalização conjuntos','',report['method'],'','| Ajuste | Recorte | MAE | Spearman | Pares na ordem correta |','|---|---|---:|---:|---:|']
    for name,result in results.items():
        for key,m in result['reports'].items():lines.append(f"| {name} | {key} | {m['mae']:.3f} | {m['spearman']:.3f} | {100*m['ordered_pairs_correct']:.1f}% |")
    lines+=['','## Transferência entre recortes','','| Treinamento | Avaliação | MAE | Spearman |','|---|---|---:|---:|']
    for origin,tests in transfers.items():
        for key,m in tests.items():lines.append(f"| {origin} | {key} | {m['mae']:.3f} | {m['spearman']:.3f} |")
    lines+=['','## Contradições de monotonicidade','']
    for key,items in conflicts.items():lines.append(f'- {key}: {len(items)} pares em que um jogador tem todas as quatro métricas maiores ou iguais, mas score menor.')
    lines+=['','## Limitações','']+['- '+s for s in report['limitations']]
    Path('docs/TRINITY_NORMALIZATION_TEST.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()

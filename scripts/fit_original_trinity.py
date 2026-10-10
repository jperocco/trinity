"""Approximate user-provided Trinity report, not future fantasy points."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import nnls
from scipy.stats import spearmanr

FEATURES = ['target_share', 'yprr', 'air_yard_share', 'redzone_targets_per_game']
SCALES = np.array([40., 4., 50., 3.])


def matrix(rows, transform):
    transform = transform.removeprefix('saturation_')
    raw = np.array([[r['target_share'], r['yprr'], r['air_yard_share'], r['redzone_targets']/r['games']] for r in rows])
    scaled = raw/SCALES
    if transform == 'capped': scaled = np.minimum(scaled, 1.)
    elif transform == 'log': scaled = np.log1p(scaled)
    return scaled


def fit(x, y, anchored=False):
    # Nonnegative coefficients and intercept: more opportunity cannot lower score.
    if anchored:
        return np.r_[0., nnls(x, -np.log1p(-y/10.))[0]]
    return nnls(np.column_stack([np.ones(len(x)), x]), y)[0]


def predict(x, beta, anchored=False):
    value = np.column_stack([np.ones(len(x)), x])@beta
    return 10*(-np.expm1(-value)) if anchored else np.clip(value, 0., 10.)


def main():
    rows = json.loads(Path('data/research/trinity_reference/top12_week4.json').read_text())
    y = np.array([r['score'] for r in rows])
    candidates = []
    for transform in ['linear', 'capped', 'log', 'saturation_linear', 'saturation_capped', 'saturation_log']:
        anchored = transform.startswith('saturation_')
        x = matrix(rows, transform)
        for mask in range(1, 16):
            columns = [i for i in range(4) if mask & (1 << i)]
            design = x[:, columns]
            beta = fit(design, y, anchored)
            p = predict(design, beta, anchored)
            loo = np.zeros(len(y))
            for i in range(len(y)):
                keep = np.arange(len(y)) != i
                loo[i] = predict(design[i:i+1], fit(design[keep], y[keep], anchored), anchored)[0]
            full = np.zeros(4)
            full[columns] = beta[1:]
            weights = full/full.sum() if full.sum() else full
            candidates.append(dict(transform=transform, features=[FEATURES[i] for i in columns], intercept=float(beta[0]),
                coefficients=dict(zip(FEATURES, full.tolist())), normalized_component_weights=dict(zip(FEATURES, weights.tolist())),
                mae=float(np.abs(p-y).mean()), max_error=float(np.abs(p-y).max()), loo_mae=float(np.abs(loo-y).mean()),
                spearman=float(spearmanr(y,p).statistic), predictions=p.tolist()))
    candidates.sort(key=lambda r: (r['loo_mae'], len(r['features']), r['mae']))
    best = candidates[0]
    anchored_best = next(c for c in candidates if c['transform'].startswith('saturation_'))
    report = dict(objective='Approximate scores in original report; not PPR prediction', reference_n=len(rows),
        anchored_best=anchored_best,
        scales=dict(zip(FEATURES, SCALES.tolist())), best=best, candidates=candidates,
        limitations=['12 visible top-ranked players only, including one TE; cannot establish full-universe ranking or position-specific weights.',
            'Leave-one-out measures interpolation within this selected report, not independent validation; candidate selection also uses these rows.',
            'Displayed input rounding limits identifiability; several weight combinations can fit similarly.',
            'Weights depend on the declared metric normalization; they are not recovered proprietary weights.',
            'Red-zone targets missing in JJ are never filled with zero. Reference metrics used directly to isolate formula fit from source differences.',
            '0–10 clipping and nonnegative intercept/coefficients are approximation assumptions.'])
    Path('docs/ORIGINAL_TRINITY_FIT.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    model = dict(status='Candidate approximation; not deployed', cutoff='2026 weeks 1–4', transform=best['transform'],
        scales=report['scales'], intercept=best['intercept'], coefficients=best['coefficients'], weights=best['normalized_component_weights'],
        output='10*(1-exp(-sum(coefficient*transformed(metric/scale))))' if best['transform'].startswith('saturation_') else 'clip(intercept + sum(coefficient × transformed(metric/scale)), 0, 10)', limitations=report['limitations'])
    Path('models/trinity_original_approx_v01.json').write_text(json.dumps(model, indent=2)+'\n')
    lines = ['# Aproximação do Trinity original', '', 'Referência: 12 jogadores visíveis no relatório fornecido, semanas 1–4. Testadas 90 combinações: 15 subconjuntos das quatro métricas, com transformação linear, teto ou logaritmo, com intercepto ou saturação ancorada em zero. Coeficientes não negativos. Seleção por erro leave-one-out; resultado exploratório.', '', '| Transformação | Métricas | MAE | MAE leave-one-out | Spearman |', '|---|---|---:|---:|---:|']
    for c in candidates[:8]:
        lines.append(f"| {c['transform']} | {', '.join(c['features'])} | {c['mae']:.4f} | {c['loo_mae']:.4f} | {c['spearman']:.3f} |")
    lines += ['', '## Pesos do candidato', '', 'Pesos relativos aos componentes normalizados; o intercepto participa do score e não está nesses percentuais. Escalas TS=40%, YPRR=4, AY share=50%, RZ targets/jogo=3.', '']
    lines += [f'- {k}: {100*v:.1f}%' for k,v in best['normalized_component_weights'].items()]
    lines += ['', f"Intercepto: {best['intercept']:.4f}. Transformação: {best['transform']}. Erro máximo na referência: {best['max_error']:.4f}.", '', '## Limitações', '']+['- '+s for s in report['limitations']]
    lines += ['', '## Alternativa ancorada em zero', '', f"Melhor candidata que dá score zero sem oportunidade: {anchored_best['transform']}; MAE {anchored_best['mae']:.4f}; leave-one-out {anchored_best['loo_mae']:.4f}.", '', 'Modelos com intercepto alto reproduzem o topo mas dão score alto sem oportunidade: não devem ser extrapolados para toda a liga. Nenhum candidato foi promovido ao painel.']
    Path('docs/ORIGINAL_TRINITY_FIT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(best, indent=2))
    print('ANCHORED', json.dumps(anchored_best))
    for r,p in zip(rows,best['predictions']): print(r['player'], r['score'], round(p,3))


if __name__ == '__main__': main()

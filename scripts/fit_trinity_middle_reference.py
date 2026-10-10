"""Test original-score approximation on newly supplied middle-ranked report."""
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from fit_original_trinity import FEATURES, SCALES, matrix, fit, predict


def evaluate(rows):
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
            loo = []
            for i in range(len(y)):
                keep = np.arange(len(y)) != i
                loo.append(predict(design[i:i+1], fit(design[keep], y[keep], anchored), anchored)[0])
            full = np.zeros(4); full[columns] = beta[1:]
            weights = full/full.sum() if full.sum() else full
            candidates.append(dict(transform=transform, features=[FEATURES[i] for i in columns], intercept=float(beta[0]),
                coefficients=dict(zip(FEATURES, full.tolist())), normalized_component_weights=dict(zip(FEATURES, weights.tolist())),
                mae=float(np.abs(p-y).mean()), max_error=float(np.abs(p-y).max()), loo_mae=float(np.abs(np.array(loo)-y).mean()),
                spearman=float(spearmanr(y,p).statistic), predictions=p.tolist()))
    return sorted(candidates, key=lambda c:(c['loo_mae'], len(c['features']), c['mae']))


def main():
    rows = json.loads(Path('data/research/trinity_reference/middle22_new_capture.json').read_text())
    old = json.loads(Path('models/trinity_original_anchored_v01.json').read_text())
    beta = np.array([old['intercept']] + [old['coefficients'][f] for f in FEATURES])
    p = predict(matrix(rows, old['transform']), beta, True)
    y = np.array([r['score'] for r in rows])
    candidates = evaluate(rows)
    best = candidates[0]
    anchored = next(c for c in candidates if c['transform'].startswith('saturation_'))
    report = dict(reference_n=len(rows), position_counts={pos:sum(r['position']==pos for r in rows) for pos in ['WR','TE']},
        source='Two user-provided screenshots 2026-10-09 23:49:25 and 23:49:54; visible ranks 17–28 and 31–40',
        period='Unconfirmed cutoff; two players have GP=5. Kept separate from earlier top12 with max GP=4.',
        constant_reference_mae=float(np.abs(y-y.mean()).mean()),
        old_anchored_transfer=dict(mae=float(np.abs(p-y).mean()),max_error=float(np.abs(p-y).max()),spearman=float(spearmanr(y,p).statistic)),
        best=best,anchored_best=anchored,scales=dict(zip(FEATURES,SCALES.tolist())),candidates=candidates,
        limitations=['22 selected middle-ranked rows, not full league; 10 TE and 12 WR.',
            'The new capture includes five-game players: merging with earlier four-game snapshot would confound calibration and period changes.',
            'Four shown metrics do not identify all original formula inputs or normalization; leave-one-out and candidate selection use this same selected sample.',
            'Normalized component weights are conditional on scales and transformations, not recovered proprietary weights.',
            'Nonnegative models can fail to reproduce rankings even when numerical score error is small.',
            'No source reconciliation, position-specific correction, manual player adjustment or production model change performed.'])
    Path('docs/ORIGINAL_TRINITY_MIDDLE_FIT.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    lines=['# Trinity original: ampliação para o meio do ranking','',report['source'],'',report['period'],'',
        f"A candidata anterior, sem novo ajuste, tem MAE {report['old_anchored_transfer']['mae']:.3f} e Spearman {report['old_anchored_transfer']['spearman']:.3f} no novo recorte. Um score constante igual à média da referência tem MAE {report['constant_reference_mae']:.3f}; portanto erro numérico pequeno sozinho não garante reconstrução do ranking.",'',
        '| Transformação | Componentes | MAE | Leave-one-out MAE | Spearman |','|---|---|---:|---:|---:|']
    for c in candidates[:8]:lines.append(f"| {c['transform']} | {', '.join(c['features'])} | {c['mae']:.3f} | {c['loo_mae']:.3f} | {c['spearman']:.3f} |")
    lines+=['','## Pesos da alternativa ancorada em zero','']+[f'- {f}: {100*w:.1f}%' for f,w in anchored['normalized_component_weights'].items()]
    lines+=['',f"Transformação {anchored['transform']}; MAE {anchored['mae']:.3f}; Spearman {anchored['spearman']:.3f}. Escalas TS=40%, YPRR=4, AY share=50%, RZ/jogo=3.",'','## Limitações','']+['- '+s for s in report['limitations']]
    lines+=['','## Decisão','','A candidata anterior não está confirmada: não transferiu bem ao novo recorte. Também não adotar o ajuste de intercepto, que aproxima os números comprimindo a faixa e reproduz mal a ordem. Pesos ficam exploratórios; não alterar o painel. Reproduzir com `python scripts/fit_trinity_middle_reference.py`, usando a transcrição local `data/research/trinity_reference/middle22_new_capture.json`. Capturas e transcrição permanecem locais.']
    Path('docs/ORIGINAL_TRINITY_MIDDLE_FIT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['candidates']},indent=2))


if __name__=='__main__':main()

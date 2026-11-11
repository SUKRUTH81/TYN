"""Offline HTML presentation of validated report artifacts; no model requests."""
import html
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


def esc(value):
    return html.escape(str(value), quote=True)


def evidence_link(ref):
    url = str(ref.get('url', ''))
    try:
        parsed = urlsplit(url)
    except ValueError:
        return esc(ref.get('key', 'Evidence'))
    label = esc(ref.get('key', 'Evidence'))
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
        return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{label} ↗</a>'
    return label


def write_visual_report(directory):
    directory = Path(directory)
    report = json.loads((directory / 'report.json').read_text(encoding='utf-8'))
    metrics_file = directory / 'metrics.json'
    metrics = json.loads(metrics_file.read_text(encoding='utf-8')) if metrics_file.exists() else {}
    rows = report.get('requirements', [])
    complete = report.get('assessment_complete') is True
    counts = Counter(row.get('decision') for row in rows if row.get('assessment_status') == 'COMPLETE')
    errors = sum(row.get('assessment_status') != 'COMPLETE' for row in rows)
    finished = len(rows) - errors
    cards = []
    colors = {'PASS': 'pass', 'FAIL': 'fail', 'INSUFFICIENT_EVIDENCE': 'unknown'}
    for row in rows:
        evaluated = row.get('assessment_status') == 'COMPLETE'
        decision = row.get('decision', 'Unknown') if evaluated else 'NOT ASSESSED'
        color = colors.get(decision, 'error')
        evidence = []
        for ref in row.get('evidence', []):
            metadata = ' · '.join(str(ref[k]) for k in ('actor', 'role', 'recorded_at') if ref.get(k))
            evidence.append(f'<div class="evidence"><div>{evidence_link(ref)} '
                f'<span class="muted">Comment {esc(ref.get("comment_id", ""))} · {esc(ref.get("stance", ""))}</span></div>'
                f'<blockquote>{esc(ref.get("quote", ""))}</blockquote><div class="muted">{esc(metadata)}</div>'
                f'<p>{esc(ref.get("note", ""))}</p></div>')
        cards.append(f'<article class="requirement {color}"><div class="row"><h2>{esc(row.get("source_id", ""))}</h2>'
            f'<span class="badge {color}">{esc(decision.replace("_", " "))}</span></div>'
            f'<p class="criterion">{esc(row.get("criterion", "Investigation did not finish"))}</p>'
            f'<p class="muted">{"Mandatory" if row.get("mandatory") else "Optional"} · '
            f'Execution: {esc(row.get("assessment_status", "Unknown"))}</p>'
            f'<p>{esc(row.get("explanation", ""))}</p>'
            f'<div class="action"><strong>Outstanding action</strong><p>{esc(row.get("outstanding", "None"))}</p></div>'
            f'<details><summary>Evidence ({len(evidence)})</summary>{"".join(evidence) or "<p>No evidence was cited.</p>"}</details></article>')
    summary = ''.join(f'<div class="stat {color}"><strong>{number}</strong><span>{label}</span></div>'
        for label, number, color in [('Pass', counts['PASS'], 'pass'), ('Fail', counts['FAIL'], 'fail'),
            ('Insufficient evidence', counts['INSUFFICIENT_EVIDENCE'], 'unknown'), ('Not assessed', errors, 'error')])
    target = ''.join(f'<div><dt>{esc(k.replace("_", " "))}</dt><dd>{esc(v)}</dd></div>' for k, v in report.get('target', {}).items())
    warnings = ''.join(f'<li>{esc(item.get("warning", ""))}</li>' for item in report.get('integrity_notes', []))
    notice = ('All requirement investigations completed. Review the evidence and independent audit before submission.' if complete else
              'INCOMPLETE ASSESSMENT — execution errors are not findings of missing product evidence. '
              'This report does not establish a final release decision.')
    provider_error = metrics.get('provider_error') or {}
    error = provider_error.get('message') or metrics.get('error')
    error_html = f'<details class="notice"><summary>Execution error</summary><p>{esc(error)}</p></details>' if error else ''
    tokens = metrics.get('usage', {}).get('total_tokens')
    stats = f'{finished}/{len(rows)} investigated · {esc(metrics.get("elapsed_seconds", "Unavailable"))} seconds · '
    stats += f'{esc(format(tokens, ",") if isinstance(tokens, (int, float)) else "Unavailable")} reported tokens'
    if not metrics.get('usage_complete', False):
        stats += ' · Token usage incomplete'
    document = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Release evidence report</title><style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#233149;background:#f2f5f9;line-height:1.6}
*{box-sizing:border-box}body{margin:0}main{max-width:1120px;margin:auto;padding:40px 24px}
header{background:#17283f;color:white;padding:32px;border-radius:20px}header p{color:#d1ddeb}
h1{font-size:2.2rem;margin:8px 0}h2{font-size:1.15rem;margin:0}p{overflow-wrap:anywhere}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:.8rem}.muted{color:#61718a;font-size:.9rem}
.notice{padding:18px 22px;background:#fff3d7;border:1px solid #e5bf65;border-radius:12px;margin:20px 0}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}.stat{background:white;padding:20px;border-radius:12px;border-top:4px solid}.stat strong{display:block;font-size:2rem}.stat span{color:#40516b}
.pass{border-color:#18815c}.fail{border-color:#c33c4c}.unknown{border-color:#b47a14}.error{border-color:#77869b}
.badge{border:1px solid;border-radius:20px;padding:5px 12px;font-size:.75rem;font-weight:700;background:white}
.badge.pass{color:#136746}.badge.fail{color:#a72d3c}.badge.unknown{color:#825500}.badge.error{color:#526076}
.requirement{background:white;border-left-width:5px;border-left-style:solid;padding:24px;margin:18px 0;border-radius:12px;box-shadow:0 3px 14px #17283f08}
.row{display:flex;align-items:center;justify-content:space-between;gap:15px}.criterion{font-size:1.1rem;font-weight:600}.action{background:#f5f7fa;border-radius:8px;padding:12px 16px}.action p{margin:4px 0}
details{margin-top:18px}summary{cursor:pointer;font-weight:600}a{color:#175fb0}nav{display:flex;gap:20px;margin:20px 0;flex-wrap:wrap}
.evidence{border-top:1px solid #dde3ec;margin-top:16px;padding-top:16px}blockquote{margin:14px 0;border-left:3px solid #9bb1d0;padding:8px 16px;background:#f7f9fc;white-space:pre-wrap}
dl{display:flex;gap:24px;flex-wrap:wrap;background:white;padding:20px;border-radius:12px}dt{text-transform:uppercase;font-size:.72rem;color:#61718a}dd{margin:4px 0;font-weight:600}
@media(max-width:650px){main{padding:18px 12px}.stats{grid-template-columns:repeat(2,1fr)}header{padding:22px}h1{font-size:1.7rem}.row{align-items:flex-start;flex-wrap:wrap}}
@media print{body{background:white}main{padding:0;max-width:none}header{background:white;color:#17283f;border:1px solid #ddd}header p{color:#40516b}nav{display:none}.requirement{box-shadow:none}details::details-content{content-visibility:visible}a{color:inherit}.stat{break-inside:avoid}}
</style></head><body><main>'''
    document += f'<header><div class="eyebrow">Release evidence assessment · {esc(report.get("project", ""))}</div>'
    document += f'<h1>{esc(report.get("release", ""))} · {esc(report.get("overall_decision", "Unknown"))}</h1>'
    document += f'<p>{esc(stats)}</p><p>Generated {esc(report.get("generated_at", ""))} · Provenance: {esc(report.get("provenance", "Unknown"))}</p></header>'
    document += f'<div class="notice" role="status">{esc(notice)}</div>{error_html}<div class="stats">{summary}</div><dl>{target}</dl>'
    document += '<nav aria-label="Report artifacts"><a href="report.md">Markdown report</a><a href="report.json">Report JSON</a><a href="metrics.json">Run metrics</a><a href="trace.md">Tool trace</a></nav>'
    if warnings:
        document += f'<details><summary>Integrity notes</summary><ul>{warnings}</ul></details>'
    document += ''.join(cards) + '<footer class="muted">Scenario actors and timestamps come from recorded Jira text, not native importer metadata. Open evidence sections to inspect citations. Use your browser’s Print → Save as PDF to export.</footer></main></body></html>'
    output = directory / 'report.html'
    output.write_text(document, encoding='utf-8')
    return output

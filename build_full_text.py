"""Compile reviewed CSV text; original PC control tags never come from editable cells."""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from build_resources import build_xml

from build_paths import ROOT
TAG = re.compile(r'(\{[^}]*\})')


def normalize(text):
    return ' '.join(re.sub(r'\\+n', ' ', text).split())


def wrap(text, width=240):
    lines, line, used = [], '', 0
    for char in text.replace(r'\n', '\n'):
        if char == '\n':
            lines.append(line.rstrip()); line, used = '', 0
            continue
        size = 4 if char == ' ' else 14 if '가' <= char <= '힣' else 8
        if used + size > width:
            lines.append(line.rstrip()); line, used = '', 0
        if not line and char == ' ':
            continue
        line += char; used += size
    lines.append(line.rstrip())
    return r'\n'.join(lines)


def load_translations(directory=ROOT / 'translation'):
    layout = json.loads((directory / 'layout.json').read_text(encoding='utf-8'))
    groups = collections.defaultdict(list)
    ids = set()
    for name in ('dialogue.csv', 'messages.csv'):
        with (directory / name).open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                key = f"{row['방']}:{int(row['메시지'])}"
                slot, utterance = int(row['조각']), int(row['발화'])
                expected_id = f'{key}:{slot}' + (f'/u{utterance}' if utterance else '')
                if row['id'] != expected_id or row['id'] in ids:
                    raise ValueError(f"Duplicate or changed id: {row['id']}")
                ids.add(row['id'])
                if key not in layout or slot * 2 not in layout[key]['slots']:
                    raise ValueError(f"Unknown PC display slot: {row['id']}")
                original = TAG.split(layout[key]['source'])[slot * 2]
                if row['PC원문'] != original:
                    raise ValueError(f"PC source changed: {row['id']}")
                text = row['번역문'].replace('\r\n', '\n').replace('\r', '\n').replace('\n', r'\n')
                if any(c in text for c in '{}') or any(0xe000 <= ord(c) <= 0xf8ff for c in text):
                    raise ValueError(f"Control tag or reserved marker in translation: {row['id']}")
                if not normalize(text) and row['검수상태'] != '원문 없음/제어 슬롯':
                    raise ValueError(f"Empty translation: {row['id']}")
                groups[key, slot].append((utterance, text, row))
    expected = {(key, part // 2) for key, entry in layout.items() for part in entry['slots']}
    if set(groups) != expected:
        raise ValueError(f'CSV display slots missing: {sorted(expected - set(groups))[:10]}')
    result, rows = {}, []
    for key, entry in layout.items():
        parts = TAG.split(entry['source'])
        for part in entry['slots']:
            pieces = sorted(groups[key, part // 2], key=lambda x: x[0])
            if [x[0] for x in pieces] != list(range(len(pieces))):
                raise ValueError(f'Non-contiguous utterances: {key}:{part // 2}')
            parts[part] = r'\n'.join(x[1] for x in pieces)
            rows.extend(x[2] for x in pieces)
        result[key] = ''.join(parts)
        if TAG.findall(result[key]) != TAG.findall(entry['source']):
            raise ValueError(f'PC controls changed: {key}')
    return result, layout, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-index', action='store_true')
    parser.add_argument('--no-wrap', action='store_true')
    args = parser.parse_args()
    translations, layout, rows = load_translations()
    out = ROOT / 'build' / ('full-text-renderer' if args.no_wrap else 'full-text-clean' if args.no_index else 'full-text-indexed')
    grouped = collections.defaultdict(list)
    for key, entry in layout.items():
        room, index = key.split(':')
        text = translations[key]
        if not args.no_index:
            marker = f'{"M" if room == "misc" else room.split("_")[0]}:{index} '
            text = text.replace('{scroll 0}', '{scroll 0}' + marker)
            if '{scroll 0}' not in text:
                text = text.replace('{clear 0}', '{clear 0}' + marker)
                # Leading scroll controls reset the pen; keep the index with its text.
                leading = re.match(r'^(?:\{scroll \d+\})*', text).end()
                text = text[:leading] + marker + text[leading:]
        if not args.no_wrap:
            text = ''.join(piece if TAG.fullmatch(piece) else wrap(piece) for piece in TAG.split(text))
        grouped[room].append((int(index), text))
    for room, entries in grouped.items():
        dest = out / ('misc.xml' if room == 'misc' else f'text/ROOM_{room}.xml')
        dest.parent.mkdir(parents=True, exist_ok=True)
        result = ET.Element('Strings')
        ordered = sorted(entries)
        if [i for i, _ in ordered] != list(range(len(ordered))):
            raise ValueError(f'Non-contiguous message indices: {room}')
        for _, text in ordered:
            ET.SubElement(result, 'Text').text = text
        ET.ElementTree(result).write(dest, encoding='utf-8', xml_declaration=False)
    resources = build_xml(out)
    report = {
        'room_entries': sum(len(entries) for room, entries in grouped.items() if room != 'misc'),
        'common_entries': len(grouped['misc']),
        'csv_rows': len(rows),
        'resource_rows': len(resources),
        'speaker_unconfirmed': sum(row['종류'] == '대사' and row['화자'] == '미확정' for row in rows),
        'review_status': dict(collections.Counter(row['검수상태'] for row in rows)),
        'csv_sha256': {name: hashlib.sha256((ROOT / 'translation' / name).read_bytes()).hexdigest() for name in ('dialogue.csv', 'messages.csv')},
        'timing_tags': 'Original PC controls preserved; inferred page content still needs scene review',
        'runtime_status': 'CSV compiled; actual scene output not verified',
    }
    (out / 'coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Read-only DOCX intake: ordered blocks, raw OMML, tables, media and hashes.

This script does not pretend that flattened math text is a LaTeX conversion.
Use the numbered OMML files and the rendered Word pages for equation review.
Usage: python inspect_docx.py INPUT.docx OUTPUT_DIRECTORY
"""
from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


def text_of(node):
    return ''.join(n.text or '' for n in node.iter()
                   if n.tag in (f"{{{NS['w']}}}t", f"{{{NS['m']}}}t"))


def inspect(source, output):
    source = source.resolve()
    output = output.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source == output:
        raise ValueError('Input and output paths must differ.')
    output.mkdir(parents=True, exist_ok=True)
    # Never overwrite an earlier intake: it may be the audit record of a revision.
    if any(output.iterdir()):
        raise FileExistsError(f'Output must be empty: {output}')
    (output / 'omml').mkdir()
    (output / 'media').mkdir()
    blocks, equations, media = [], [], []
    with ZipFile(source) as z:
        root = ET.fromstring(z.read('word/document.xml'))
        rels = {}
        if 'word/_rels/document.xml.rels' in z.namelist():
            rels = {n.attrib['Id']: n.attrib.get('Target', '')
                    for n in ET.fromstring(z.read('word/_rels/document.xml.rels'))}
        body = root.find('w:body', NS)
        if body is None:
            raise ValueError('DOCX document has no main body.')
        features = {name: len(root.findall('.//w:' + name, NS))
                    for name in ('ins', 'del', 'txbxContent', 'object')}
        extra_parts = [name for name in z.namelist()
                       if name.startswith(('word/header', 'word/footer',
                                           'word/footnotes', 'word/endnotes',
                                           'word/comments')) and name.endswith('.xml')]
        for index, node in enumerate(body):
            kind = node.tag.rsplit('}', 1)[-1]
            if kind == 'sectPr':
                continue
            block = {'id': index, 'type': kind, 'text': text_of(node)}
            style = node.find('w:pPr/w:pStyle', NS)
            if style is not None:
                block['style'] = style.get(f"{{{NS['w']}}}val")
            block['equations'] = []
            for math in node.findall('.//m:oMath', NS):
                number = len(equations) + 1
                name = f'omml/equation-{number:02d}.xml'
                (output / name).write_bytes(ET.tostring(math, encoding='utf-8'))
                equations.append({'id': number, 'block': index, 'file': name,
                                  'flattened_preview_not_latex': text_of(math)})
                block['equations'].append(number)
            if kind == 'tbl':
                block['rows'] = [[text_of(cell) for cell in row.findall('w:tc', NS)]
                                 for row in node.findall('w:tr', NS)]
            block['images'] = [rels.get(blip.get(f"{{{NS['r']}}}embed"), '')
                               for blip in node.findall('.//a:blip', NS)]
            blocks.append(block)
        for name in z.namelist():
            if name.startswith('word/media/') and not name.endswith('/'):
                filename = Path(name).name
                data = z.read(name)
                (output / 'media' / filename).write_bytes(data)
                media.append({'file': f'media/{filename}',
                              'sha256': hashlib.sha256(data).hexdigest()})
        (output / 'document.xml').write_bytes(z.read('word/document.xml'))
    manifest = {
        'source_name': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'separate_review': {'body_features': features, 'package_parts': extra_parts},
        'counts': {'blocks': len(blocks), 'equations': len(equations),
                   'tables': sum(b['type'] == 'tbl' for b in blocks), 'media': len(media)},
        'blocks': blocks, 'equations': equations, 'media': media,
        'limitations': 'Inspect formulas in OMML and Word rendering. Plain text loses fraction, radical, superscript and matrix structure. Embedded OLE equations, text boxes, revisions, headers and footnotes may require separate inspection.',
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'ordered-text.md').write_text(
        '# Word 原文顺序提取\n\n公式预览不是 LaTeX，必须对照 OMML 和渲染页。\n\n' +
        '\n\n'.join(f"## 源块 {b['id']:03d} ({b['type']})\n\n{b['text']}" for b in blocks),
        encoding='utf-8')
    print(json.dumps(manifest['counts']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    inspect(args.source, args.output)

"""Xuất toàn bộ đồ thị Neo4j (node, quan hệ, constraint/index) ra một file Cypher nạp lại được.

Không cần APOC: đọc bằng Python driver rồi tự sinh Cypher. Mỗi câu lệnh nằm trên một dòng, kết thúc bằng ';'.
    docker compose exec api python -m ml.export_graph --out knowledge/knowledge_graph.cypher
Nạp lại vào Neo4j RỖNG (cùng bản 5.x):
    cypher-shell -u neo4j -p <mật khẩu> -f knowledge_graph.cypher

- MERGE theo khoá ổn định của từng nhãn (NODE_KEYS); nhãn phụ (vd Entity:Symptom) được SET thêm.
- Thứ tự tất định (nhãn, khoá; loại quan hệ, khoá hai đầu; property theo tên) để diff giữa hai lần xuất có nghĩa;
  chỉ dòng thời điểm xuất ở header thay đổi.
- Fail fast khi dữ liệu không xuất đúng được: node không có nhãn khoá hoặc thiếu khoá, khoá trùng, quan hệ song song
  cùng loại (MERGE sẽ gộp mất), giá trị NaN/vô cực, kiểu property lạ, loại index chưa hỗ trợ.
"""
import argparse
import json
import math
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

VN = ZoneInfo('Asia/Ho_Chi_Minh')
# Nhãn -> property làm khoá MERGE. Đã kiểm trên DB 13/11/2026: khoá không null, không trùng; Document/Entity/Topic
# có UNIQUENESS constraint trên đúng khoá này, WebSource thì không (khoá vẫn duy nhất, được kiểm khi xuất).
NODE_KEYS = {'Document': 'id', 'Entity': 'id', 'Topic': 'name', 'WebSource': 'id'}
_ESCAPES = {'\\': '\\\\', '"': '\\"', '\n': '\\n', '\r': '\\r', '\t': '\\t', '\b': '\\b', '\f': '\\f'}


def cypher_identifier(name: str) -> str:
    """Tên nhãn/loại/property trong backtick; backtick bên trong được nhân đôi."""
    if not name:
        raise ValueError('Empty identifier')
    return '`' + name.replace('`', '``') + '`'


def cypher_value(value) -> str:
    """Literal Cypher cho một giá trị property (str, bool, int, float, list các kiểu đó)."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f'Non-finite float cannot be exported: {value!r}')
        # repr: biểu diễn ngắn nhất đọc lại ra đúng float đó; Cypher không nhận dấu '+' ở số mũ (1e+20).
        return repr(value).replace('e+', 'e')
    if isinstance(value, str):
        out = []
        for ch in value:
            if ch in _ESCAPES:
                out.append(_ESCAPES[ch])
            elif ord(ch) < 0x20 or 0x7f <= ord(ch) < 0xa0 or ch in '  ':
                out.append(f'\\u{ord(ch):04x}')
            else:
                out.append(ch)   # tiếng Việt giữ nguyên UTF-8 cho dễ đọc
        return '"' + ''.join(out) + '"'
    if isinstance(value, (list, tuple)):
        return '[' + ', '.join(cypher_value(v) for v in value) + ']'
    raise TypeError(f'Unsupported property type: {type(value).__name__}')


def cypher_map(props: dict) -> str:
    return '{' + ', '.join(f'{cypher_identifier(k)}: {cypher_value(props[k])}' for k in sorted(props)) + '}'


@dataclass(frozen=True)
class Node:
    element_id: str
    labels: tuple[str, ...]
    props: dict

    @property
    def key_label(self) -> str:
        found = [label for label in self.labels if label in NODE_KEYS]
        if len(found) != 1:
            raise ValueError(f'Node {self.element_id} labels {self.labels} must have exactly one of {sorted(NODE_KEYS)}')
        return found[0]

    @property
    def key(self) -> tuple[str, str, object]:
        label = self.key_label
        prop = NODE_KEYS[label]
        if self.props.get(prop) is None:
            raise ValueError(f'Node {self.element_id} ({label}) has no key property {prop!r}')
        return label, prop, self.props[prop]

    def sort_key(self):
        label, _, value = self.key
        return label, str(value)


@dataclass(frozen=True)
class Rel:
    type: str
    start: str   # element id
    end: str
    props: dict


@dataclass(frozen=True)
class SchemaItem:
    """Constraint hoặc index cần tạo lại (đã chuẩn hoá từ SHOW CONSTRAINTS / SHOW INDEXES)."""
    kind: str            # 'UNIQUENESS' | 'RANGE'
    name: str
    label: str
    properties: tuple[str, ...]

    def cypher(self) -> str:
        target = ', '.join(f'n.{cypher_identifier(p)}' for p in self.properties)
        head = f'{cypher_identifier(self.name)} IF NOT EXISTS FOR (n:{cypher_identifier(self.label)})'
        if self.kind == 'UNIQUENESS':
            group = target if len(self.properties) == 1 else f'({target})'
            return f'CREATE CONSTRAINT {head} REQUIRE {group} IS UNIQUE;'
        if self.kind == 'RANGE':
            return f'CREATE INDEX {head} ON ({target});'
        raise ValueError(f'Unsupported schema kind {self.kind!r}')


def schema_items(constraints: list[dict], indexes: list[dict]) -> list[SchemaItem]:
    """Constraint UNIQUENESS + index RANGE tự tạo. Bỏ index LOOKUP (Neo4j tự có) và index do constraint sở hữu."""
    items = []
    for c in constraints:
        if c['type'] != 'UNIQUENESS' or len(c['labelsOrTypes']) != 1:
            raise ValueError(f"Unsupported constraint {c['name']!r} of type {c['type']!r}")
        items.append(SchemaItem('UNIQUENESS', c['name'], c['labelsOrTypes'][0], tuple(c['properties'])))
    for i in indexes:
        if i['type'] == 'LOOKUP' or i.get('owningConstraint'):
            continue
        if i['type'] != 'RANGE' or i.get('entityType', 'NODE') != 'NODE':
            raise ValueError(f"Unsupported index {i['name']!r} of type {i['type']!r}")
        items.append(SchemaItem('RANGE', i['name'], i['labelsOrTypes'][0], tuple(i['properties'])))
    return sorted(items, key=lambda s: (s.kind != 'UNIQUENESS', s.name))


def _match(node: Node, var: str) -> str:
    label, prop, value = node.key
    return f'({var}:{cypher_identifier(label)} {{{cypher_identifier(prop)}: {cypher_value(value)}}})'


def node_statement(node: Node) -> str:
    label, prop, _ = node.key
    extra = sorted(lab for lab in node.labels if lab != label)
    sets = [f'n:{cypher_identifier(lab)}' for lab in extra]
    rest = {k: v for k, v in node.props.items() if k != prop and v is not None}
    sets.append(f'n += {cypher_map(rest)}')
    return f"MERGE {_match(node, 'n')} SET {', '.join(sets)};"


def rel_statement(rel: Rel, nodes: dict[str, Node]) -> str:
    start, end = nodes[rel.start], nodes[rel.end]
    props = {k: v for k, v in rel.props.items() if v is not None}
    tail = f' SET r += {cypher_map(props)}' if props else ''
    return f"MATCH {_match(start, 'a')}, {_match(end, 'b')} MERGE (a)-[r:{cypher_identifier(rel.type)}]->(b){tail};"


def embedding_summary(nodes: list[Node]) -> list[str]:
    counts = Counter((len(n.props['embedding']), n.props.get('embedding_model') or '(không ghi model)')
                     for n in nodes if isinstance(n.props.get('embedding'), list))
    return [f'{model} {dim} chiều: {count}' for (dim, model), count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def render(nodes: list[Node], rels: list[Rel], schema: list[SchemaItem], exported_at: datetime,
           server_version: str = '') -> str:
    """Toàn bộ file Cypher. Thuần, tất định với cùng dữ liệu (thứ tự đầu vào không ảnh hưởng)."""
    if exported_at.utcoffset() is None:
        raise ValueError('exported_at must be timezone-aware')
    by_id = {n.element_id: n for n in nodes}
    keys = Counter(n.key for n in nodes)
    duplicated = [k for k, c in keys.items() if c > 1]
    if duplicated:
        raise ValueError(f'Duplicate node keys (MERGE would merge them): {duplicated[:5]}')
    missing = [r for r in rels if r.start not in by_id or r.end not in by_id]
    if missing:
        raise ValueError(f'{len(missing)} relationships point to unknown nodes')
    rel_keys = [(r.type, by_id[r.start].key, by_id[r.end].key) for r in rels]
    parallel = [k for k, c in Counter(rel_keys).items() if c > 1]
    if parallel:
        raise ValueError(f'Parallel relationships of the same type (MERGE would merge them): {parallel[:3]}')

    label_counts = Counter(':'.join(sorted(n.labels)) for n in nodes)
    type_counts = Counter(r.type for r in rels)
    header = [
        '// Neo4j knowledge graph snapshot (Đường An), tạo bởi ml/export_graph.py.',
        f"// Xuất lúc: {exported_at.astimezone(VN).isoformat(timespec='seconds')}"
        + (f' · Neo4j {server_version}' if server_version else ''),
        f'// Node: {len(nodes)}; quan hệ: {len(rels)}.',
        '// Node theo nhãn: ' + ', '.join(f'{k} {v}' for k, v in sorted(label_counts.items())),
        '// Quan hệ theo loại: ' + ', '.join(f'{k} {v}' for k, v in sorted(type_counts.items())),
        '// Embedding: ' + ('; '.join(embedding_summary(nodes)) or 'không có'),
        '// Khoá MERGE: ' + ', '.join(f'{k}.{v}' for k, v in sorted(NODE_KEYS.items())) + '.',
        '// Nạp vào Neo4j 5 RỖNG: cypher-shell -u neo4j -p <mật khẩu> -f knowledge_graph.cypher',
        '',
    ]
    body = [s.cypher() for s in schema] + ['']
    body += [node_statement(n) for n in sorted(nodes, key=Node.sort_key)] + ['']
    ordered = sorted(rels, key=lambda r: (r.type, by_id[r.start].sort_key(), by_id[r.end].sort_key()))
    body += [rel_statement(r, by_id) for r in ordered]
    return '\n'.join(header + body) + '\n'


def read_graph(db) -> tuple[list[Node], list[Rel], list[SchemaItem], str]:
    run = lambda query: db.execute_query(query, database_='neo4j').records
    nodes = [Node(r['id'], tuple(r['labels']), dict(r['props']))
             for r in run('MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props')]
    rels = [Rel(r['type'], r['start'], r['end'], dict(r['props']))
            for r in run('MATCH (a)-[r]->(b) RETURN type(r) AS type, elementId(a) AS start, elementId(b) AS end, '
                         'properties(r) AS props')]
    constraints = [r.data() for r in run('SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties')]
    indexes = [r.data() for r in run('SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties, owningConstraint')]
    version = run('CALL dbms.components() YIELD versions RETURN versions[0] AS v')[0]['v']
    return nodes, rels, schema_items(constraints, indexes), version


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', help='file đích (mặc định: stdout); ghi qua file tạm rồi thay thế')
    args = parser.parse_args(argv)
    from neo4j import GraphDatabase
    with GraphDatabase.driver(os.environ['NEO4J_URI'],
                              auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD'])) as db:
        nodes, rels, schema, version = read_graph(db)
    text = render(nodes, rels, schema, datetime.now(VN), version)
    if args.out:
        out = Path(args.out)
        tmp = out.with_suffix(out.suffix + '.tmp')
        tmp.write_text(text, encoding='utf-8')
        tmp.replace(out)
        print(json.dumps({'out': str(out), 'nodes': len(nodes), 'relationships': len(rels),
                          'bytes': out.stat().st_size}, ensure_ascii=False), file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

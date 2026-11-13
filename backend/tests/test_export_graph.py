"""Unit test phần sinh Cypher của ml/export_graph.py (không cần Neo4j)."""
import random
from datetime import datetime, timezone

import pytest

from ml.export_graph import (Node, Rel, SchemaItem, cypher_identifier, cypher_value, node_statement, render,
                             schema_items)

AT = datetime(2026, 11, 13, 2, 30, tzinfo=timezone.utc)   # = 09:30 giờ VN


def doc(eid, doc_id, **props):
    return Node(eid, ('Document',), {'id': doc_id, **props})


def test_string_escapes_quotes_backslash_and_control_characters():
    assert cypher_value('a "b" \\ c') == '"a \\"b\\" \\\\ c"'
    assert cypher_value("it's") == '"it\'s"'
    assert cypher_value('dòng 1\ndòng 2\r\tx') == '"dòng 1\\ndòng 2\\r\\tx"'
    assert cypher_value('\x00\x1f ') == '"\\u0000\\u001f\\u2028"'


def test_vietnamese_text_is_kept_readable():
    text = 'Đường huyết lúc đói ≥ 126 mg/dL – theo Bộ Y tế'
    assert cypher_value(text) == f'"{text}"'


def test_float_list_round_trips_exactly():
    values = [0.1, -0.027560467, 1e-05, 1.5e+20, 3.0, -0.0]
    literal = cypher_value(values)
    assert literal == '[0.1, -0.027560467, 1e-05, 1.5e20, 3.0, -0.0]'
    assert [float(x) for x in literal.strip('[]').split(', ')] == values


def test_scalars_and_lists_of_strings():
    assert cypher_value(True) == 'true' and cypher_value(False) == 'false'
    assert cypher_value(42) == '42'
    assert cypher_value(['a', 'b"c']) == '["a", "b\\"c"]'
    assert cypher_value([]) == '[]'


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), [1.0, float('-inf')]])
def test_non_finite_floats_fail_fast(bad):
    with pytest.raises(ValueError):
        cypher_value(bad)


def test_unsupported_types_fail_fast():
    with pytest.raises(TypeError):
        cypher_value({'nested': 1})
    with pytest.raises(TypeError):
        cypher_value(None)


def test_identifiers_are_backtick_quoted():
    assert cypher_identifier('Document') == '`Document`'
    assert cypher_identifier('we`ird') == '`we``ird`'
    with pytest.raises(ValueError):
        cypher_identifier('')


def test_node_with_secondary_label_merges_on_key_label():
    node = Node('4:x:1', ('Symptom', 'Entity'), {'id': 'khat-nuoc', 'name': 'Khát nước', 'aliases': ['khát', 'khat'],
                                               'kind': 'Symptom'})
    assert node_statement(node) == (
        'MERGE (n:`Entity` {`id`: "khat-nuoc"}) SET n:`Symptom`, '
        'n += {`aliases`: ["khát", "khat"], `kind`: "Symptom", `name`: "Khát nước"};')


def test_topic_merges_on_name():
    assert node_statement(Node('t', ('Topic',), {'name': 'Chẩn đoán'})) == \
        'MERGE (n:`Topic` {`name`: "Chẩn đoán"}) SET n += {};'


@pytest.mark.parametrize('node', [Node('x', ('Unknown',), {'id': 'a'}), Node('x', ('Document',), {'title': 't'}),
                                  Node('x', ('Document', 'Topic'), {'id': 'a', 'name': 'b'})])
def test_nodes_without_a_single_usable_key_fail_fast(node):
    with pytest.raises(ValueError):
        node_statement(node)


def graph():
    nodes = [doc('e1', 'b-doc', text='Nội dung "trích"\nxuống dòng', embedding=[0.5, -0.25]),
             doc('e2', 'a-doc', text='A', embedding=[0.1, 0.2], embedding_model='bge-m3'),
             Node('e3', ('Topic',), {'name': 'Chẩn đoán'}),
             Node('e4', ('Entity', 'Disease'), {'id': 'dtd', 'name': 'Đái tháo đường'})]
    rels = [Rel('ABOUT', 'e1', 'e3', {}), Rel('ABOUT', 'e2', 'e3', {}),
            Rel('DESCRIBED_IN', 'e4', 'e2', {'source_url': 'https://x', 'note': None})]
    schema = [SchemaItem('UNIQUENESS', 'document_id', 'Document', ('id',))]
    return nodes, rels, schema


def test_render_is_deterministic_regardless_of_input_order():
    nodes, rels, schema = graph()
    expected = render(nodes, rels, schema, AT, '5.26.32')
    rng = random.Random(7)
    for _ in range(5):
        rng.shuffle(nodes)
        rng.shuffle(rels)
        assert render(nodes, rels, schema, AT, '5.26.32') == expected


def test_render_layout_header_schema_nodes_then_relationships():
    text = render(*graph(), AT, '5.26.32')
    lines = text.splitlines()
    assert '// Xuất lúc: 2026-11-13T09:30:00+07:00 · Neo4j 5.26.32' in lines
    assert '// Node: 4; quan hệ: 3.' in lines
    assert '// Node theo nhãn: Disease:Entity 1, Document 2, Topic 1' in lines
    assert '// Quan hệ theo loại: ABOUT 2, DESCRIBED_IN 1' in lines
    assert '// Embedding: (không ghi model) 2 chiều: 1; bge-m3 2 chiều: 1' in lines
    statements = [line for line in lines if line and not line.startswith('//')]
    assert statements[0] == 'CREATE CONSTRAINT `document_id` IF NOT EXISTS FOR (n:`Document`) REQUIRE n.`id` IS UNIQUE;'
    assert [s.split('{')[1].split('}')[0] for s in statements[1:3]] == ['`id`: "a-doc"', '`id`: "b-doc"']
    assert statements[-1] == ('MATCH (a:`Entity` {`id`: "dtd"}), (b:`Document` {`id`: "a-doc"}) '
                              'MERGE (a)-[r:`DESCRIBED_IN`]->(b) SET r += {`source_url`: "https://x"};')
    assert statements[-3].endswith('MERGE (a)-[r:`ABOUT`]->(b);')
    assert all(s.endswith(';') for s in statements)
    assert '\\"trích\\"\\nxuống dòng' in text and text.endswith(';\n')


def test_header_time_is_vietnam_time_for_any_input_zone():
    naive = datetime(2026, 11, 13, 9, 30)
    with pytest.raises(ValueError):
        render(*graph(), naive)
    assert '2026-11-13T09:30:00+07:00' in render(*graph(), AT)


def test_duplicate_keys_and_parallel_relationships_fail_fast():
    nodes, rels, schema = graph()
    with pytest.raises(ValueError, match='Duplicate node keys'):
        render(nodes + [doc('e9', 'a-doc')], rels, schema, AT)
    with pytest.raises(ValueError, match='Parallel relationships'):
        render(nodes, rels + [Rel('ABOUT', 'e1', 'e3', {'x': 'y'})], schema, AT)
    with pytest.raises(ValueError, match='unknown nodes'):
        render(nodes, rels + [Rel('ABOUT', 'e1', 'missing', {})], schema, AT)


def test_schema_keeps_constraints_and_own_range_indexes_only():
    constraints = [{'name': 'topic_name', 'type': 'UNIQUENESS', 'labelsOrTypes': ['Topic'], 'properties': ['name']},
                   {'name': 'document_id', 'type': 'UNIQUENESS', 'labelsOrTypes': ['Document'], 'properties': ['id']}]
    indexes = [{'name': 'document_id', 'type': 'RANGE', 'entityType': 'NODE', 'labelsOrTypes': ['Document'],
                'properties': ['id'], 'owningConstraint': 'document_id'},
               {'name': 'index_343aff4e', 'type': 'LOOKUP', 'entityType': 'NODE', 'labelsOrTypes': None,
                'properties': None, 'owningConstraint': None},
               {'name': 'doc_topic', 'type': 'RANGE', 'entityType': 'NODE', 'labelsOrTypes': ['Document'],
                'properties': ['topic'], 'owningConstraint': None}]
    items = schema_items(constraints, indexes)
    assert [i.cypher() for i in items] == [
        'CREATE CONSTRAINT `document_id` IF NOT EXISTS FOR (n:`Document`) REQUIRE n.`id` IS UNIQUE;',
        'CREATE CONSTRAINT `topic_name` IF NOT EXISTS FOR (n:`Topic`) REQUIRE n.`name` IS UNIQUE;',
        'CREATE INDEX `doc_topic` IF NOT EXISTS FOR (n:`Document`) ON (n.`topic`);']


def test_unsupported_index_types_fail_fast():
    vector = {'name': 'emb', 'type': 'VECTOR', 'entityType': 'NODE', 'labelsOrTypes': ['Document'],
              'properties': ['embedding'], 'owningConstraint': None}
    with pytest.raises(ValueError, match='Unsupported index'):
        schema_items([], [vector])

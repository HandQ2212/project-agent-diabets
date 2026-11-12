import pytest


@pytest.fixture(autouse=True)
def no_live_knowledge_graph(monkeypatch, request):
    """Các test API không kết nối Neo4j thật; test riêng của đồ thị dùng FakeDB."""
    if request.module.__name__.endswith('test_knowledge_graph'):
        return
    from backend.app import knowledge_graph
    monkeypatch.setattr(knowledge_graph, 'lookup', lambda question, db=None: None)

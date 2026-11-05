import httpx
import pytest
from ml.refresh_web import MainText, fetch, make_chunks, valid_url
from backend.app.rag import answer


def test_extracts_main_and_ignores_navigation_and_scripts():
    parser = MainText()
    parser.feed('<nav><p>Ignore navigation text that is long enough</p></nav><main><h2>Diabetes information for adults</h2><script>ignore this</script><p>Important <b>public health</b> information here.</p></main>')
    assert parser.blocks == ['Diabetes information for adults', 'Important public health information here.']
    assert all(len(chunk) <= 40 for chunk in make_chunks(parser.blocks, limit=40))


def test_web_fetch_rejects_untrusted_redirect():
    transport = httpx.MockTransport(lambda req: httpx.Response(302, headers={'location': 'https://evil.example/'}))
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ValueError, match='allowed'):
            fetch(client, 'https://www.cdc.gov/diabetes/')
    assert not valid_url('http://www.cdc.gov/')
    assert not valid_url('https://www.cdc.gov.evil.example/')


def test_web_fetch_rejects_oversized_response():
    transport = httpx.MockTransport(lambda req: httpx.Response(200, headers={'content-type': 'text/html'}, content=b'x' * 2_000_001))
    with httpx.Client(transport=transport) as client:
        with pytest.raises(ValueError, match='size limit'):
            fetch(client, 'https://www.cdc.gov/diabetes/')

def test_unreviewed_web_source_is_not_summarized_by_llm(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Unreviewed web content must not be sent for generation')
    monkeypatch.setattr('backend.app.rag.httpx.post', forbidden)
    result = answer('Triệu chứng là gì?', [{'title': 'CDC', 'url': 'https://www.cdc.gov/', 'text': 'Unreviewed', 'review_status': 'unreviewed_web'}])
    assert 'chưa được kiểm duyệt' in result
    assert '[1]' in result


def test_topic_boost_requires_combined_diabetes_question_and_manual_summary():
    from backend.app.rag import _topic_boost
    doc = {'title': 'WHO: Các loại đái tháo đường và phòng ngừa típ 2',
           'topic': 'Các loại tiểu đường và cách phòng ngừa', 'review_status': None}
    assert _topic_boost('Có những loại tiểu đường nào và cách phòng tránh?', doc) > 0
    assert _topic_boost('Cách nấu phở bò như thế nào?', doc) == 0
    assert _topic_boost('Các loại tiểu đường và cách phòng tránh?', {**doc, 'review_status': 'unreviewed_web'}) == 0

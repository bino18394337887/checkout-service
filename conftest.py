import pytest
from app.checkout_service import app

@pytest.fixture
def client():
    """Flask测试客户端 (测试模式，无需手动启动服务)"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
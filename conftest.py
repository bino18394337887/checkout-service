import pytest
from app.checkout_service import app

@pytest.fixture
def client():
    """Flask测试客户端（无需手动启动服务）"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="module")
def base_url():
    """基础接口URL（用于并发测试）"""
    return "http://127.0.0.1:5000/checkout"
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.checkout_service import app  # 直接导入Flask应用实例

# ------------------- 功能测试（保持不变，继续使用client fixture）-------------------
@pytest.mark.parametrize("input_data, expected_status, expected_response", [
    # 正常场景
    ({"items": [{"price": 20, "quantity": 3}]}, 200, {"total": 60, "status": "ok"}),
    ({"items": [{"price": 15.5, "quantity": 2}, {"price": 30, "quantity": 1}]}, 200, {"total": 61.0, "status": "ok"}),
    ({"items": [{"price": 0, "quantity": 10}]}, 200, {"total": 0, "status": "ok"}),
    ({"items": [{"price": 50, "quantity": 0}]}, 200, {"total": 0, "status": "ok"}),
    ({"items": []}, 400, {"error": "empty cart"}),
    # 异常场景
    ({"items": [{"quantity": 2}]}, 400, {"error": "invalid item: missing price or quantity"}),
    ({"items": [{"price": 20}]}, 400, {"error": "invalid item: missing price or quantity"}),
    ({"items": [{"price": "twenty", "quantity": 3}]}, 400, {"error": "invalid item: price/quantity must be number"}),
    ({"items": [{"price": 20, "quantity": "three"}]}, 400, {"error": "invalid item: price/quantity must be number"}),
])
def test_checkout_functionality(client, input_data, expected_status, expected_response):
    response = client.post("/checkout", json=input_data)
    assert response.status_code == expected_status
    assert {k: v for k, v in response.json.items() if k != "details"} == expected_response

# ------------------- 并发测试（核心重构：完全独立的线程上下文）-------------------
def test_checkout_concurrency():  # 关键：不传入client fixture
    input_data = {"items": [{"price": 20, "quantity": 3}]}
    concurrent_num = 5
    expected_total = 60
    results = []

    def send_test_request():
        """每个线程创建独立客户端+独立上下文，完全隔离"""
        try:
            # 1. 每个线程创建独立的测试客户端（不共享fixture的client）
            with app.test_client() as thread_client:
                # 2. 包裹「应用上下文 + 请求上下文」，确保线程独立
                with app.app_context(), thread_client.test_request_context():
                    # 3. 用当前线程的客户端发请求
                    response = thread_client.post("/checkout", json=input_data)
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "total": response.json.get("total") if response.status_code == 200 else None
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 执行并发请求
    with ThreadPoolExecutor(max_workers=concurrent_num) as executor:
        futures = [executor.submit(send_test_request) for _ in range(concurrent_num)]
        for future in as_completed(futures):
            results.append(future.result())

    # 验证结果
    for result in results:
        assert result["success"] is True, f"并发请求失败：{result.get('error')}"
        assert result["status_code"] == 200
        assert result["total"] == expected_total
    assert len(results) == concurrent_num
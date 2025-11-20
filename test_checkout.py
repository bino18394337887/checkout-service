import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.checkout_service import app  # 关键：导入Flask应用实例

# 功能测试（无需修改，保持之前的正确逻辑）
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

# 并发测试（核心修复：手动隔离Flask上下文）
def test_checkout_concurrency(client):
    input_data = {"items": [{"price": 20, "quantity": 3}]}
    concurrent_num = 5
    expected_total = 60
    results = []

    # 关键：每个并发任务手动管理应用上下文
    def send_test_request():
        try:
            # 手动推入应用上下文（确保当前线程有独立上下文）
            with app.app_context():
                # 执行测试请求（client会自动管理请求上下文）
                response = client.post("/checkout", json=input_data)
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "total": response.json.get("total") if response.status_code == 200 else None
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 执行并发请求（保持不变）
    with ThreadPoolExecutor(max_workers=concurrent_num) as executor:
        futures = [executor.submit(send_test_request) for _ in range(concurrent_num)]
        for future in as_completed(futures):
            results.append(future.result())

    # 验证结果（保持不变）
    for result in results:
        assert result["success"] is True, f"并发请求失败：{result.get('error')}"
        assert result["status_code"] == 200
        assert result["total"] == expected_total
    assert len(results) == concurrent_num
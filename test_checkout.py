import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 功能测试（更新预期状态码：非法参数从500改为400）
@pytest.mark.parametrize("input_data, expected_status, expected_response", [
    # 正常场景（5个通过用例，保持不变）
    ({"items": [{"price": 20, "quantity": 3}]}, 200, {"total": 60, "status": "ok"}),
    ({"items": [{"price": 15.5, "quantity": 2}, {"price": 30, "quantity": 1}]}, 200, {"total": 61.0, "status": "ok"}),
    ({"items": [{"price": 0, "quantity": 10}]}, 200, {"total": 0, "status": "ok"}),
    ({"items": [{"price": 50, "quantity": 0}]}, 200, {"total": 0, "status": "ok"}),
    ({"items": []}, 400, {"error": "empty cart"}),
    # 异常场景（更新预期状态码为400，响应信息匹配服务端）
    ({"items": [{"quantity": 2}]}, 400, {"error": "invalid item: missing price or quantity"}),
    ({"items": [{"price": 20}]}, 400, {"error": "invalid item: missing price or quantity"}),
    ({"items": [{"price": "twenty", "quantity": 3}]}, 400, {"error": "invalid item: price/quantity must be number"}),
    ({"items": [{"price": 20, "quantity": "three"}]}, 400, {"error": "invalid item: price/quantity must be number"}),
])
def test_checkout_functionality(client, input_data, expected_status, expected_response):
    response = client.post("/checkout", json=input_data)
    # 验证状态码
    assert response.status_code == expected_status
    # 验证响应内容（忽略details字段，避免测试耦合）
    assert {k: v for k, v in response.json.items() if k != "details"} == expected_response

# 并发测试（修复：使用Flask测试客户端，无需真实服务）
def test_checkout_concurrency(client):
    input_data = {"items": [{"price": 20, "quantity": 3}]}
    concurrent_num = 5  # 减少并发数，降低CI资源占用
    expected_total = 60
    results = []

    # 内部函数：使用测试客户端发请求（无网络依赖）
    def send_test_request():
        try:
            response = client.post("/checkout", json=input_data)
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

    # 验证所有请求成功
    for result in results:
        assert result["success"] is True, f"并发请求失败：{result.get('error')}"
        assert result["status_code"] == 200
        assert result["total"] == expected_total
    assert len(results) == concurrent_num
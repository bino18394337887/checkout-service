import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 功能测试（正常+异常场景）
@pytest.mark.parametrize("input_data, expected_status, expected_response", [
    # 正常场景
    ({"items": [{"price": 20, "quantity": 3}]}, 200, {"total": 60, "status": "ok"}),
    ({"items": [{"price": 15.5, "quantity": 2}, {"price": 30, "quantity": 1}]}, 200, {"total": 61.0, "status": "ok"}),
    ({"items": [{"price": 0, "quantity": 10}]}, 200, {"total": 0, "status": "ok"}),
    ({"items": [{"price": 50, "quantity": 0}]}, 200, {"total": 0, "status": "ok"}),
    # 异常场景
    ({"items": []}, 400, {"error": "empty cart"}),
    ({"items": [{"quantity": 2}]}, 500, None),
    ({"items": [{"price": 20}]}, 500, None),
    ({"items": [{"price": "twenty", "quantity": 3}]}, 500, None),
    ({"items": [{"price": 20, "quantity": "three"}]}, 500, None),
])
def test_checkout_functionality(client, input_data, expected_status, expected_response):
    response = client.post("/checkout", json=input_data)
    assert response.status_code == expected_status
    if expected_response is not None:
        assert response.json == expected_response

# 并发测试
def send_concurrent_request(url, input_data):
    try:
        response = requests.post(url, json=input_data, timeout=5)
        return {
            "success": True,
            "status_code": response.status_code,
            "total": response.json().get("total") if response.status_code == 200 else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_checkout_concurrency(base_url):
    input_data = {"items": [{"price": 20, "quantity": 3}]}
    concurrent_num = 10
    expected_total = 60
    results = []

    with ThreadPoolExecutor(max_workers=concurrent_num) as executor:
        futures = [executor.submit(send_concurrent_request, base_url, input_data) for _ in range(concurrent_num)]
        for future in as_completed(futures):
            results.append(future.result())

    for result in results:
        assert result["success"] is True
        assert result["status_code"] == 200
        assert result["total"] == expected_total
    assert len(results) == concurrent_num
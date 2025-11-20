from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/checkout", methods=["POST"])
def checkout():
    try:
        data = request.get_json()
        items = data.get("items", [])
        
        # 1. 空购物车校验（原有逻辑）
        if not items:
            return jsonify({"error": "empty cart"}), 400
        
        # 2. 遍历商品，校验每个商品的合法性
        total = 0
        for item in items:
            # 校验是否缺少必填字段（price/quantity）
            if "price" not in item or "quantity" not in item:
                return jsonify({"error": "invalid item: missing price or quantity"}), 400
            
            # 校验price和quantity是否为数字（int/float）
            price = item["price"]
            quantity = item["quantity"]
            if not isinstance(price, (int, float)) or not isinstance(quantity, (int, float)):
                return jsonify({"error": "invalid item: price/quantity must be number"}), 400
            
            # 校验数量是否为非负（避免负数订单）
            if quantity < 0:
                return jsonify({"error": "invalid item: quantity cannot be negative"}), 400
            
            # 累加总价
            total += price * quantity
        
        return jsonify({"total": total, "status": "ok"}), 200
    
    # 捕获其他意外异常（如JSON格式错误）
    except Exception as e:
        return jsonify({"error": "server error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000)
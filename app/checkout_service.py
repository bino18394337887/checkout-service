from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "empty cart"}), 400
    total = sum(i["price"] * i["quantity"] for i in items)
    return jsonify({"total": total, "status": "ok"}), 200

if __name__ == "__main__":
    app.run(port=5000)
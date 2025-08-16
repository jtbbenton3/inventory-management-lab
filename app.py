from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(port=5555, debug=True)
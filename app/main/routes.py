from flask import request, render_template
from app.main import bp



@bp.route('/', methods=["GET"])
def index():
    if request.method == "GET":
        return render_template("index.html")
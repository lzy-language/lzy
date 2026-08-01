# TODO: replace this with something better instead of ai slop
import io
import contextlib

from flask import Flask, render_template, request, jsonify

from lzy_env import Environment, StrictError, StopSignal
from lzy_eval import Evaluator
from lzy_run import run, show_vars

app = Flask(__name__)

env = Environment()
evaluator = Evaluator(env)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_code():

    code = request.json.get("code", "")

    output = io.StringIO()

    try:
        with contextlib.redirect_stdout(output):
            run(code, env, evaluator)

    except StrictError as e:
        print(f"[strict assert] {e}", file=output)

    except StopSignal:
        pass

    except Exception as e:
        print(f"[error] {e}", file=output)

    return jsonify({
        "output": output.getvalue()
    })


@app.route("/vars")
def vars_route():

    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        show_vars(env)

    return jsonify({
        "output": output.getvalue()
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

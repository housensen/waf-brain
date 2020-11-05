import aiofiles
import logging
import re

from sanic import response, Blueprint

from waf_brain.inferring import process_payload

log = logging.getLogger("waf-brain")

waf_blueprint_simulator = Blueprint("waf_brain_simulator")


pattern = re.compile("^[A-Za-z0-9_-]*$")

@waf_blueprint_simulator.route('/<path:[\w\W\/]*>',
                               methods=[
                                   "GET",
                                   "POST",
                                   "PUT",
                                   "DELETE",
                                   "HEAD",
                                   "OPTIONS"
                               ])
async def waf_simulator(request, path):
    MODEL = request.app.config["MODEL"]
    BLOCKING_THRESHOLD = request.app.config["BLOCKING_THRESHOLD"]
    DUMP_FILE = request.app.config["DUMP_FILE"]

    total = []       
    for arg, val in request.query_args:
        if pattern.match(val):
            total.append(
                {"paramName": arg,
                "score": 0,
                "time": 0,
                "weights": 0}
            )
        else:
            print(process_payload)
            total.append(process_payload(
                MODEL,
                arg,
                [val],
                True
            ))

    async with aiofiles.open(DUMP_FILE, 'a+') as f:

        await f.writelines(
            [
                f"[sec: {t['time']:.5f}] param: '{t['paramName']}' "
                f"- Scoring: {t['score']} - "
                f"track-id:"
                f"{request.headers.get('WAF-BENCHMARK-TRACK-ID')}\n"
                f"{t['weights']}\n"
                for t in total
            ]
            )

    #
    # Request must be block if the WAF detect and attack?
    #
    if any(x["score"] >= BLOCKING_THRESHOLD for x in total):
        return response.text("Dangerous request detected and blocked",
                             status=403)

    else:
        return response.text("OK", status=200)


__all__ = ("waf_blueprint_simulator", )

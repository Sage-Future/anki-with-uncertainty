import json

from aqt import gui_hooks, mw, reviewer
from aqt.qt import *
from aqt.utils import qconnect, showInfo

addon_dir = mw.addonManager.addonFromModule(__name__)
base_path = os.path.join(mw.addonManager.addonsFolder(), addon_dir)
calibration_data_path = os.path.join(base_path, "user_files/calibration_data.json")

COMMAND = "updateCalibration;"

def updateCalibration(handled, message, context):
    handleAndPreventDefault = (True, None)
    
    if not message.startswith(COMMAND):
        return handled # pass on message

    if not isinstance(context, reviewer.Reviewer):
        return handleAndPreventDefault

    payload = message[len(COMMAND):]
    with open(calibration_data_path, "a+") as f:
        f.write(payload + "\n")

    print("Wrote calibration data to file:" + str(payload) + " " + str(base_path) + "/user_files/calibration_data.json")
    return handleAndPreventDefault

gui_hooks.webview_did_receive_js_message.append(updateCalibration)


def getCalibrationScores():
    if not os.path.exists(calibration_data_path):
        raise RuntimeError("Calibration data file does not exist. Answer some interval questions first.")

    with open(calibration_data_path, "r") as f:
        lines = f.readlines()

        if not lines:
            raise RuntimeError("Calibration data file is empty. Answer some interval questions first!")

        answers = [json.loads(line.strip()) for line in lines if line != ""]
        confidence_intervals = set(answer["confidenceInterval"] for answer in answers)
        
        scores = {}
        for interval in sorted(confidence_intervals):
            interval_answers = [answer for answer in answers if answer["confidenceInterval"] == interval]
            scores[interval] = {
                "Correct": str(round(sum(answer["correct"] for answer in interval_answers) / len(interval_answers) * 100, 2)) + "%",
                "Questions answered": len(interval_answers),
                "Mean score": mean([answer["score"] for answer in interval_answers]),
                "Median score": median([answer["score"] for answer in interval_answers]),
            }

        return scores

def mean(items):
    return sum(items) / len(items)

def median(items):
    items = sorted(items)
    if len(items) % 2 == 0:
        return mean(items[len(items) // 2 - 1 : len(items) // 2 + 1])
    else:
        return items[len(items) // 2]

def printScores():
    try:
        all_scores = getCalibrationScores()
        output = "Your calibration scores so far:\n\n"
        for confidence_interval, scores in all_scores.items():
            score_str = "\n".join(["    " + str(k) + ": " + (str(round(v, 2)) if isinstance(v, float) else v) for k, v in scores.items()])
            output += str(confidence_interval) + r"% confidence interval:\n" + score_str + "\n\n"
        showInfo(output)

    except RuntimeError as e:
        showInfo("Could not read calibration data: " + str(e))


# add to the tools menu
action = QAction("Show calibration scores", mw)
qconnect(action.triggered, printScores)
mw.form.menuTools.addAction(action)

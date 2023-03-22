import json
from statistics import mean, median

from aqt import gui_hooks, mw, reviewer
from aqt.qt import *
from aqt.utils import qconnect, showInfo

addon_dir = mw.addonManager.addonFromModule(__name__)
base_path = os.path.join(mw.addonManager.addonsFolder(), addon_dir)
calibration_data_path = os.path.join(base_path, "user_files/calibration_data.json")

COMMAND = "updateCalibration;"

def updateCalibration(handled: tuple[bool, any], message: str, context: any):
    handleAndPreventDefault = (True, None)
    
    if not message.startswith(COMMAND):
        return handled # pass on message

    if not isinstance(context, reviewer.Reviewer):
        return handleAndPreventDefault

    payload = message[len(COMMAND):]
    with open(calibration_data_path, "a+") as f:
        f.write(payload + "\n")

    print(f"Wrote calibration data to file: {payload} {base_path}/user_files/calibration_data.json")
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
                "Correct": f'{round(sum(answer["correct"] for answer in interval_answers) / len(interval_answers) * 100, 2)}%',
                "Questions answered": len(interval_answers),
                "Mean score": mean(answer["score"] for answer in interval_answers),
                "Median score": median(answer["score"] for answer in interval_answers),
            }

        return scores

def printScores():
    try:
        all_scores = getCalibrationScores()
        output = "Your calibration scores so far:\n\n"
        for confidence_interval, scores in all_scores.items():
            score_str = "\n".join([f"    {k}: {round(v, 2) if isinstance(v, float) else v}" for k, v in scores.items()])
            output += f"{confidence_interval}% confidence interval:\n{score_str}\n\n"
        showInfo(output)

    except RuntimeError as e:
        showInfo(f"Could not read calibration data: {e}")


# add to the tools menu
action = QAction("Show calibration scores", mw)
qconnect(action.triggered, printScores)
mw.form.menuTools.addAction(action)

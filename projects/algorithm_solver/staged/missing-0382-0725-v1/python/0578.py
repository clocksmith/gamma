"""578. Get Highest Answer Rate Question. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. survey_log: id, action, question_id, answer_id, q_num, timestamp. Output: survey_log. Counts retain duplicate rows; zero-show ratios sort as SQL NULL after numeric ratios."""

def solve(survey_log):
    counts = {}
    for row in survey_log:
        pair = counts.setdefault(row['question_id'], [0, 0])
        pair[0] += row['action'] == 'answer'
        pair[1] += row['action'] == 'show'
    best = None
    for question in sorted(counts):
        answer, show = counts[question]
        if best is None:
            best = question
        else:
            old_answer, old_show = counts[best]
            if show and (not old_show or answer * old_show > old_answer * show):
                best = question
    return [] if best is None else [{'survey_log': best}]


class Solution:
    def highestAnswerRate(self, survey_log):
        return solve(survey_log)

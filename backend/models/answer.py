class Answer:
    def __init__(self, id, interview_id, question_text, answer_text=None, wpm=None, clarity_score=None):
        self.id = id
        self.interview_id = interview_id
        self.question_text = question_text
        self.answer_text = answer_text
        self.wpm = wpm
        self.clarity_score = clarity_score
#!/usr/bin/env python

from bot import Question, AnswerType

questions = [
    Question("Wie lange hast du geschlafen?", "qme.seri.bot.sleep", AnswerType.hm_timespan),
]

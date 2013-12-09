#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import select
import logging
from threading import Thread
from Queue import Queue

import xmpp

import config
import questions

log = logging.getLogger("qme-bot")

in_messages = None

class AnswerType(object):
    @staticmethod
    def hm_timespan(raw):
        """HH:MM return minutes"""

        h, m = map(int, raw.split(":"))

        assert 0 <= h
        assert 0 <= m <= 59

        return h*60 + m

class Question(object):
    def __init__(self, question, path, convert):
        self.question = question
        self.path = path
        self.convert = convert

class EventHandler(Thread):
    def __init__(self, client):
        Thread.__init__(self)
        self.client = client
        self.daemon = True

    def run(self):
        self.eventloop()

    def eventloop(self):
        epoll = select.epoll()
        epoll.register(self.client.Connection._sock.fileno(), select.EPOLLIN)

        while True:
            evs = epoll.poll(maxevents=1)
            for fileno, ev in evs:
                self.client.Process(1)

def xmpp_init(jid, password):
    jid = xmpp.protocol.JID(jid)
    client = xmpp.Client(jid.getDomain(),debug=[])

    c = client.connect()
    if not c:
        log.error('could not connect!', c)
    else:
        log.info('Connected: %s', c)

    auth = client.auth(jid.getNode(), password, resource=jid.getResource())


    if not auth:
        log.error('Could not authenticate :(')
        return False
    else:
        log.info('Authenticated: %s', auth)


    client.sendInitPresence()

    global in_messages
    in_messages = Queue()
    client.RegisterHandler('message', message_handler)

    return client

def message_handler(connection, event):
    msg_type = event.getType()
    msg = event.getBody()
    from_jid = event.getFrom().getStripped()

    if msg_type in ['message', 'chat', None]:
        log.info('Message from "%s" recvd: %s', from_jid, msg)
        in_messages.put(msg)


def ask_questions(tojid, client, questions):
    def say(msg):
        client.send(xmpp.protocol.Message(tojid, msg))

    def ask(question):
        say(question.question)

    def complain():
        say("I didn't get that. Could you please repeat?")

    def wait_for_answer(question):
        q = False

        for raw in iter(in_messages.get, None):
            try:
                q = question.convert(raw)
                return q

            except Exception, e:
                complain()
                log.error("Answer conversion failed: %s", e)


    say("HAI time to answer some questions:")

    for question in questions:
        ask(question)

        answer = wait_for_answer(question)

        log.info("Answer: %s", answer)

    say("KTHXBAI!")


def setup_logger():
    logf = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logh = logging.StreamHandler()
    logh.setLevel(logging.DEBUG)
    logh.setFormatter(logf)

    log.addHandler(logh)
    log.setLevel(logging.DEBUG)


def main():
    if len(sys.argv) < 2:
        print "Syntax: bot JID"
        sys.exit(0)

    tojid=sys.argv[1]

    setup_logger()

    client = xmpp_init(config.jid, config.password)

    handler = EventHandler(client)
    handler.start()

    ask_questions(tojid, client, questions.questions)

    sys.exit(0)

if __name__ == '__main__':
    main()

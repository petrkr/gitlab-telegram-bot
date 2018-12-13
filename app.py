#!/usr/bin/env python3

import json
from flask import Flask
from flask import request
from flask import jsonify
from bot import Bot
app = Flask(__name__)

class GitlabBot(Bot):
    def __init__(self):
        try:
            self.authmsg = open('authmsg').read().strip()
        except:
            raise Exception("The authorization messsage file is invalid")

        super(GitlabBot, self).__init__()
        self.chats = {}
        try:
            chats = open('chats', 'r').read()
            self.chats = json.loads(chats)
        except:
            open('chats', 'w').write(json.dumps(self.chats))

        self.send_to_all('Hi !')

    def text_recv(self, txt, chatid):
        ''' registering chats '''
        txt = txt.strip()
        if txt.startswith('/'):
            txt = txt[1:]
        if txt == self.authmsg:
            if str(chatid) in self.chats:
                self.reply(chatid, "\U0001F60E  boy, you already got the power.")
            else:
                self.reply(chatid, "\U0001F60E  Ok boy, you got the power !")
                self.chats[chatid] = True
                open('chats', 'w').write(json.dumps(self.chats))
        elif txt == 'shutupbot':
            del self.chats[chatid]
            self.reply(chatid, "\U0001F63F Ok, take it easy\nbye.")
            open('chats', 'w').write(json.dumps(self.chats))
        else:
            self.reply(chatid, "\U0001F612 I won't talk to you.")

    def send_to_all(self, msg):
        for c in self.chats:
            self.reply(c, msg)


b = GitlabBot()


@app.route("/", methods=['GET', 'POST'])
def webhook():
    data = request.json
    # json contains an attribute that differenciates between the types, see
    # https://docs.gitlab.com/ce/user/project/integrations/webhooks.html
    # for more infos
    kind = data['object_kind']
    if kind == 'push':
        msg = generatePushMsg(data)
    elif kind == 'tag_push':
        msg = generatePushMsg(data)  # TODO:Make own function for this
    elif kind == 'issue':
        msg = generateIssueMsg(data)
    elif kind == 'note':
        msg = generateCommentMsg(data)
    elif kind == 'merge_request':
        msg = generateMergeRequestMsg(data)
    elif kind == 'wiki_page':
        msg = generateWikiMsg(data)
    elif kind == 'pipeline':
        msg = generatePipelineMsg(data)
    elif kind == 'build':
        msg = generateBuildMsg(data)
    b.send_to_all(msg)
    return jsonify({'status': 'ok'})


def generatePushMsg(data):
    msg = '*{0} ({1}) - {2} new commits*\n'\
        .format(data['project']['name'], data['project']['default_branch'], data['total_commits_count'])
    for commit in data['commits']:
        msg = msg + '----------------------------------------------------------------\n'
        msg = msg + commit['message'].rstrip()
        msg = msg + '\n' + commit['url'].replace("_", "\_") + '\n'
    msg = msg + '----------------------------------------------------------------\n'
    return msg


def generateIssueMsg(data):
    action = data['object_attributes']['action']
    if action == 'open':
        msg = '*{0} new Issue for {1}*\n'\
            .format(data['project']['name'], data['assignee']['name'])
    elif action == 'close':
        msg = '*{0} Issue closed by {1}*\n'\
            .format(data['project']['name'], data['user']['name'])
    msg = msg + '*{0}*'.format(data['object_attributes']['title'])
    msg = msg + 'see {0} for further details'.format(data['object_attributes']['url'])
    return msg


def generateCommentMsg(data):
    ntype = data['object_attributes']['noteable_type']
    if ntype == 'Commit':
        msg = 'note to commit'
    elif ntype == 'MergeRequest':
        msg = 'note to MergeRequest'
    elif ntype == 'Issue':
        msg = 'note to Issue'
    elif ntype == 'Snippet':
        msg = 'note on code snippet'
    return msg


def generateMergeRequestMsg(data):
    return 'new MergeRequest'


def generateWikiMsg(data):
    return 'new wiki stuff'


def getEmojiStatus(status):
    if status == "success":
        return "✔"

    if status == "running":
        return "▶"

    return "❓"


def generatePipelineMsg(data):
    msg = '{0}'.format(getEmojiStatus(data['object_attributes']['status']))
    print("pipeline trigger")
    if data['object_attributes']['status'] == 'running':
        msg = msg + '{0} #{1} (by {2})\n'.format(data['project']['path_with_namespace'], data['object_attributes']['id'], data['user']['username'])
    else:
        msg = msg + '*{0} #{1} (by {2})*\n'.format(data['project']['path_with_namespace'], data['object_attributes']['id'], data['user']['username'])
    return msg


def generateBuildMsg(data):
    msg = ''
    msg = msg + 'build #'+str(data['build_id'])+' commit #'+str(data['commit']['id'])+' '+str(data['build_status'])+'\n'
    return msg


if __name__ == "__main__":
    b.run_threaded()
    app.run(host='0.0.0.0', port=10111)

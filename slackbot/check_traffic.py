from flask import Flask, request, make_response, Response
import os
import json
from helper import validate_input
from tower_api import launch_job, get_job_template
from slackclient import SlackClient
import time
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# Your app's Slack bot user token
SLACK_VERIFICATION_TOKEN = "WaHR8XYGsLQnzsGtvGARlJbx"
SLACK_BOT_TOKEN = "xoxb-272971091299-429555003410-g2JGZGpq7AIzU26YRaHq4uRy"
TOWER_HOSTNAME = ''
TOWER_USERNAME = ''
TOWER_PASSWORD = ''

# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)

# Flask web server for incoming traffic from Slack
app = Flask(__name__)
USER_INPUT = {}

@app.route("/validate", methods=["POST"])
def validate():
    user_id = request.form["user_id"]
    data = request.form.items()
    print(data)
    print()
    open_dialog = slack_client.api_call("dialog.open",
                                        trigger_id=request.form["trigger_id"],
                                        dialog={
                                            "title": "Validate network traffic",
                                            "callback_id": "Network-Validate-Traffic",
                                            "elements": [
                                                {"label": "Source network",
                                                 "type": "text",
                                                 "name": "source_network",
                                                 "placeholder": "192.168.0.0/24"},
                                                {"label": "Destination network",
                                                 "type": "text",
                                                 "name": "destination_network",
                                                 "placeholder": "10.168.32.0/24"},
                                                {"label": "protocol",
                                                 "type": "text",
                                                 "name": "protocol",
                                                 "placeholder": "tcp/udp/ip"},
                                                {"label": "destination port",
                                                 "type": "text",
                                                 "name": "port",
                                                 "placeholder": "8443"},
                                                {"label": "permitted or denied?",
                                                 "type": "text",
                                                 "name": "action",
                                                 "placeholder": "permit"}
                                            ]
                                          }
                                        )
    print(open_dialog)
    return make_response("",200)

@app.route("/deploy", methods=["POST"])
def confirm():
    user_id = request.form["user_id"]
    data = request.form.items()
    print(data)
    print()
    open_dialog = slack_client.api_call("dialog.open",
                                        trigger_id=request.form["trigger_id"],
                                        dialog={
                                            "title": "Confirm Deployment",
                                            "callback_id": "Network-Caretaker-Deploy",
                                            "elements": [
                                                {"label": "Confirm Deployment",
                                                 "type": "select",
                                                 "name": "Confirm Deployment to Production",
                                                 "options": [
                                                    {
                                                      "label": "Deploy to Production",
                                                      "value": "Deploy"
                                                    },
                                                    {
                                                      "label": "Cancel Deployment",
                                                      "value": "Cancel"
                                                    }
                                                ]
                                              }
                                            ]
                                          }
                                        )
    print(open_dialog)
    return make_response("",200)

@app.route("/reconcile", methods=["POST"])
def reconcile():
    user_id = request.form["user_id"]
    data = request.form.items()
    print(data)
    print()
    open_dialog = slack_client.api_call("dialog.open",
                                        trigger_id=request.form["trigger_id"],
                                        dialog={
                                            "title": "Reconciliation",
                                            "callback_id": "Network-Reconcile",
                                            "elements": [
                                                {"label": "Reconcile OOB Change",
                                                 "type": "select",
                                                 "name": "Reconcile OOB Change",
                                                 "options": [
                                                    {
                                                      "label": "Update Device(s)",
                                                      "value": "sync_to_devices"
                                                    },
                                                    {
                                                      "label": "Update SoT",
                                                      "value": "sync_to_sot"
                                                    }
                                                ]
                                              }
                                            ]
                                          }
                                        )
    print(open_dialog)
    return make_response("",200)

###Entry Point for Adding New Functionality

def call_tower(user_input, job_template):
    template_name = job_template
    login_creds = dict(host_name="ansible.rhdemo.io", user_name="chatops", pass_word="Ch@tops123")
    template_uri = get_job_template(template_name, **login_creds)
    return launch_job(template_uri, user_input, **login_creds)

@app.route("/interactive-component", methods=["POST"])
def dialog():
    user_input = {}
    message = json.loads(request.form["payload"])
    job_template = message['callback_id']
    channel_id = message['channel']['id']
    user = message['user']['name']
    return_data = ":white_check_mark: Received @{} ! I'm working on it!".format(user)
    result = slack_client.api_call(
     "chat.postMessage",
     channel=channel_id,
     ts=message["action_ts"],
     text=return_data,

        )

    if message['callback_id'] == 'Network-Validate-Traffic':
        user_input['extra_vars'] = validate_input(message['submission'])
        user_input['extra_vars']['slack_user'] = user
    #
    if message['callback_id'] == 'Network-Caretaker-Deploy':
        user_input['extra_vars'] = {}
        user_input['extra_vars']['slack_user'] = user

    if message['callback_id'] == 'Network-Reconcile':
        user_input['extra_vars'] = {}
        user_input['extra_vars']['slack_user'] = user
        user_input['job_tags'] = message['submission']['Reconcile OOB Change']

    # Execute Job Template
    tower_response = call_tower(user_input, job_template)
    slack_client.api_call(
     "chat.postMessage",
     channel=channel_id,
     text = "I've fired off " + job_template + " Ansible Tower job for you"
     )
    return make_response("", 200)

if __name__ == "__main__":
    #Add check's for TOWER_VARS & SLACK_VARS being declared
    app.run(debug=True, host='0.0.0.0', port='8888')

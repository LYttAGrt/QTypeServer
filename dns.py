from flask import Flask, request
import json


class QtypeDNS:
    """
        DNS storage: str ID -> [str ADDR, ? PORT, bool ONLINE, str CALLSTO]
    """

    def __init__(self, filepath='./dns.json'):
        self.filepath = filepath
        try:
            with open(self.filepath, 'r') as fd:
                self.__dns: dict = json.load(fp=fd)
        except FileNotFoundError or json.JSONDecodeError:
            self.__dns = {'DNS': {'addr': 'localhost', 'port': 5000, 'online': True, 'callsto': ''}}

    # Renames
    def rename_user(self, old_id: str, new_id: str):
        # Rename?
        if old_id in self.__dns.keys() and new_id not in self.__dns.keys():
            self.__dns[new_id] = self.__dns.pop(old_id)
            if self.__dns[new_id]['callsto'] != '':
                self.__dns[self.__dns[new_id]['callsto']]['callsto'] = new_id
            return "Renamed successfully!"
        else:
            return "New alias already exists!"

    # Returns a dictionary of USER as alias -> BOOLEAN as is it available
    def list_active_users(self):
        active_users = {}
        for user in self.__dns:
            if self.__dns[user]['online'] and user != 'DNS':
                active_users[user] = {'alias': user, 'status': False if self.__dns[user]['callsto'] != '' else True}
        return active_users

    # Registers the user status.
    def register_addr(self, alias: str, addr: str, status: str, port: int):
        if alias not in self.__dns.keys():
            self.__dns[alias] = {'addr': addr, 'port': port, 'online': status, 'callsto': ''}
            print(self.__dns)
            return "New address registered!"
        else:
            # Become online
            if status == 'join' or status == "true":
                self.__dns[alias]['online'] = True
                print(self.__dns)
                return "Address registered, you're online!"
            # Become offline
            if status == 'exit' or status == "false":
                self.__dns[alias]['online'] = False
                print(self.__dns)
                return "Address registered, you're offline!"
        # Anyway, return OK
        print(self.__dns)
        return "Nothing occured!"

    # Start call by SELF_ID to USER_ID
    def get_user_addr(self, self_id: str, user_id: str):
        res = {'addr': self.__dns[user_id]['addr'], 'port': self.__dns[user_id]['port']}
        if self.__dns[user_id]['callsto'] == '':
            self.__dns[self_id]['callsto'] = user_id
            self.__dns[user_id]['callsto'] = self_id
            res['call'] = True
        else:
            res['call'] = False
        print(self.__dns)
        return res

    # End call by CALLER_ID. Autochecking allowed.
    def confirm_call_end(self, caller_id: str):
        callee_id = self.__dns[caller_id]['callsto']
        if callee_id != '':
            self.__dns[caller_id]['callsto'] = ''
            self.__dns[callee_id]['callsto'] = ''
        print(self.__dns)
        return "{} and {} finished call.".format(caller_id, callee_id)

    def save_storage(self):
        with open(self.filepath, 'w+') as fd:
            fd.write(json.dumps(self.__dns))
            fd.flush()
        return 0


app = Flask(__name__)
dns = QtypeDNS()


@app.route('/dns/list', methods=['GET'])
def get_list_of_active_users():
    return dns.list_active_users()


@app.route('/dns/rename', methods=['GET'])
def rename_user():
    cur_alias = request.args.get(key='alias', default='DNS')
    new_alias = request.args.get(key='new_alias', default='DNS')
    return dns.rename_user(cur_alias, new_alias), 200


@app.route('/dns/register', methods=['GET'])
def register_addr():
    status = request.args.get(key='status', default=False)
    cur_alias = request.args.get(key='alias', default='DNS')
    user_addr, user_port = request.remote_addr, request.args.get(key='port', default='20000')
    return dns.register_addr(alias=cur_alias, addr=user_addr, status=status, port=user_port), 200


@app.route('/dns/call', methods=['GET'])
def get_addr():
    self_alias = request.args.get(key='alias', default='DNS')
    user_alias = request.args.get(key='other_alias', default='DNS')
    return dns.get_user_addr(self_id=self_alias, user_id=user_alias), 200


@app.route('/dns/free', methods=['GET'])
def end_call():
    self_alias = request.args.get(key='alias', default='DNS')
    return dns.confirm_call_end(self_alias), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)
    dns.save_storage()
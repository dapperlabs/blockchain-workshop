from flask import Flask, request
from node import Node

app =  Flask(__name__)

node = Node()

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    req_data = request.get_json()
    required_fields = ["transaction"]

    for field in required_fields:
        if not req_data.get(field):
            return "Invalid request: missing field transaction", 400    

    node.new_transaction(req_data)

    return "Success", 201


node.new_transaction("test1")
node.mine()
print(node.blockchain)
print('----')
node.new_transaction("test2")
node.mine()
print(node.blockchain)
print('----')
node.new_transaction("test3")
node.mine()
print(node.blockchain)
print('----')
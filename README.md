# Blockchain Workshop
This repository contains code for a simple and educational blockchain node in Python. Multiple instances of this code, if connected, form a multi-node blockchain. These instances can be run on different computers, or the same computer using different ports. You can issue commands and get information from the node using HTTP RESTful endpoints.

## Installation
You will need `python3` and `pip3` to run this code. First clone the repo:
```
git clone https://github.com/dapperlabs/blockchain-workshop.git
```
Install requirements:
```
pip3 install -r requirements3.8.txt
```
Run the code on local computer's port `5000`:
```
python3 app.py 5000
```
If you see the below output you're set!
```
[2020-02-28 18:03:38,935 - INFO] Address generated for node: MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuCKsK+OtbmyvO4Lya9tLslxlkKDwwE7SVJHfmWB4EuLIF6pGcbE1R6w1AIckDA9EP6Jjw0YktW4gP2883WEvjWvPBIJW+JhjRLOuuwKla2FkjnbTVDz3q8csGXiHpy7m7xsIdG6eW7OOznENgu0ahDwWDxy5rRm3SfrMOBxFqYG/CAw2YbItOOBpJogkn1PnLm/s2IcO25k2OahRkdeukh1xiHhQEEkN4/SMe6KRFpH5RSth1tv7IAgUxBJ6kFr7FWHeMZXFZntl5ecHmMs2d+SS0oH6DYTn839hMfTTcZ8C0/yxQU3WT8V/l/2eq+Var1JjJcHtH1OqrrYtkpHb0QIDAQAB
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
[2020-02-28 18:03:38,956 - INFO]  * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```
Open your browser and navigate to `http://localhost:5000/info`. You should see:
```
{"chain_size": 0, "peers": [], "blocks": []}
```

**Note** Depending on your system you may have to use `pip` instead of `pip3`, `python` instead of `python3` or you may need to use `sudo` with the above commands. Let us know if you have trouble with the setup!

## Endpoints Reference
The code provides these RESTful endpoints:
* `GET /info` gives basic information about this node. This endpoint returns the current blockchain size, a list of this node's peers and the full blockchain dump for this node. You can use this to debug your node. This endpoint is also used, when another peer wants to sync with this node's blockchain.
* `POST /new_transaction` creates a new transaction! You need to provide `to` and `amount`. It creates a new transaction moving coins from this node's wallet to the address specified in `to` (which may be invalid!). This transaction is added to the node's transaction pool until it is mined in a block, and thus valid on our blockchain!
* `GET /start_mining` instructs a node to start mining. This will return an error if the node is already mining.
* `GET /stop_mining` instructs a node to stop mining. This will return an error if the node is already stopped.
* `GET /balances` returns a list of all addresses along with their balances, according to this node's version of the blockchain balances do not include transactions not yet mined, it also has everyones balance because in our and most other  blockchains everybody knows what everybody else owns!
* `GET /tx_pool` returns list of transactions in the transaction pool. These transactions are created but not yet mined! Remember transactions in tx_pool are not yet executed by the blockchain. They will be final when they are mined in a block.
* `POST /add_peer` adds a new peer to our node and syncs with it. It needs `address` field in the request to identify the peer. This endpoint adds the peer to the node's list and calls consensus. Consensus checks the blockchain size on all peers (including the new one) and syncs with the longest chain.
* `POST /greet` greets another node who wants to sync with this node. It needs `address` field in the request to identify the peer. Retrurns `get_info` to the new node.
* `GET /consensus` calls `/greet` on all known peers to find out about their blockchain and its size. It then syncs with the node with the longest blockchain.
* `POST /new_block_mined` is used to receive new blocks from the network as they are mined. This endpoint needs the JSON dump of the new block. An important thing to note here is the node checks the new block closely to make sure it is valid for our current version of the chain. If the new block is valid it's also propagated to our peer list so others know about this block. This is an important function to keep all nodes in sync with each other's version of the blockchain. 

We suggest using Postman to interact with your node, you can import the `ubc-blockchain-workshop.postman_collection.json` for a collection of requests. You can also use `curl` if you are on Linux or Mac and feel adventurous!



## Goal
Start with the code in the `start` directory. Read the code and try to understand what's happening. The code is fully commented and feel free to ask questions if you don't understand a concept. You'll see 3 steps marked in the code as `STEP1`, `STEP2` and `STEP3`. Complete the code on these steps as the goal of workshop! You can see the complete solution in the `solution` directory.

**Psst** There are hints in the `start` directory!

### Step 1
The goal of this step is to start mining on our node! Check out `node.py` and you'll find two places in the code marked as `STEP1`. Write the correct code in their place to get mining. To check your work, run the node and call the `start_mining` endpoint. You should be able to see your node mining new blocks.
```
[2020-02-28 18:32:50,732 - INFO] Genesis block created!
[2020-02-28 18:32:50,733 - INFO] 127.0.0.1 - - [28/Feb/2020 18:32:50] "GET /start_mining HTTP/1.1" 200 -
[2020-02-28 18:32:50,735 - INFO] Mining block 2 ... [difficulty=10] [target=003fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:50,742 - INFO] Block 2 mined!
[2020-02-28 18:32:50,742 - INFO] Announcing block 2 to 0 peers ...
[2020-02-28 18:32:50,744 - INFO] Mining block 3 ... [difficulty=11] [target=001fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:50,957 - INFO] Block 3 mined!
[2020-02-28 18:32:50,957 - INFO] Announcing block 3 to 0 peers ...
[2020-02-28 18:32:50,958 - INFO] Mining block 4 ... [difficulty=12] [target=000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:51,069 - INFO] Block 4 mined!
[2020-02-28 18:32:51,069 - INFO] Announcing block 4 to 0 peers ...
[2020-02-28 18:32:51,070 - INFO] Mining block 5 ... [difficulty=13] [target=0007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:51,076 - INFO] Block 5 mined!
[2020-02-28 18:32:51,076 - INFO] Announcing block 5 to 0 peers ...
[2020-02-28 18:32:51,077 - INFO] Mining block 6 ... [difficulty=14] [target=0003ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:51,580 - INFO] Block 6 mined!
[2020-02-28 18:32:51,580 - INFO] Announcing block 6 to 0 peers ...
[2020-02-28 18:32:51,581 - INFO] Mining block 7 ... [difficulty=15] [target=0001ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:51,606 - INFO] Block 7 mined!
[2020-02-28 18:32:51,607 - INFO] Announcing block 7 to 0 peers ...
[2020-02-28 18:32:51,608 - INFO] Mining block 8 ... [difficulty=16] [target=0000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:52,431 - INFO] Block 8 mined!
[2020-02-28 18:32:52,431 - INFO] Announcing block 8 to 0 peers ...
[2020-02-28 18:32:52,433 - INFO] Mining block 9 ... [difficulty=17] [target=00007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:53,267 - INFO] Block 9 mined!
[2020-02-28 18:32:53,267 - INFO] Announcing block 9 to 0 peers ...
[2020-02-28 18:32:53,269 - INFO] Mining block 10 ... [difficulty=18] [target=00003fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
[2020-02-28 18:32:53,573 - INFO] Block 10 mined!
[2020-02-28 18:32:53,573 - INFO] Announcing block 10 to 0 peers ...
[2020-02-28 18:32:53,574 - INFO] Mining block 11 ... [difficulty=19] [target=00001fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
```

### Step 2
On step 2, we will sync a new node with a running one! You can use two terminals to run two instances on different ports. Check out `app.py` and search for `STEP2`. Fix the code, fire up one instance and start mining. Then use `add_peer` to sync the second instance with the first one. You should see an output like this on the second node:
```
[2020-02-28 18:48:48,650 - INFO] New peer added: http://127.0.0.1:5000
[2020-02-28 18:48:48,650 - INFO] Running consensus ...
[2020-02-28 18:48:48,686 - INFO] Syncing ... dump size: 9 current size: 0
[2020-02-28 18:48:48,686 - INFO] Block 1 processed successfully!
[2020-02-28 18:48:48,687 - INFO] Block 2 processed successfully!
[2020-02-28 18:48:48,687 - INFO] Block 3 processed successfully!
[2020-02-28 18:48:48,688 - INFO] Block 4 processed successfully!
[2020-02-28 18:48:48,689 - INFO] Block 5 processed successfully!
[2020-02-28 18:48:48,689 - INFO] Block 6 processed successfully!
[2020-02-28 18:48:48,690 - INFO] Block 7 processed successfully!
[2020-02-28 18:48:48,690 - INFO] Block 8 processed successfully!
[2020-02-28 18:48:48,691 - INFO] Block 9 processed successfully!
[2020-02-28 18:48:48,691 - INFO] Loaded successfully!
```

### Step 3
Transactions! Find `STEP3` in `node.py` and write the code that creates the transaction. You should be able to call `new_transaction` on your node with the following output:
```
[2020-02-28 19:01:03,728 - INFO] Transaction 1 to test added to transaction pool!
[2020-02-28 19:01:03,729 - INFO] 127.0.0.1 - - [28/Feb/2020 19:01:03] "POST /new_transaction HTTP/1.1" 201 -
```

### Optional Step
Let's do something cooler! Fire up three instances on three ports, connect them together and mine on all three of them. Does your blockchain stay in sync? You can also try connecting to other student's computers and nodes. Your node works on any network! You don't need to fix code in order for this to happen.

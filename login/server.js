const express = require("express");
const Web3 = require("web3");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
app.use(bodyParser.json());
app.use(cors());

const web3 = new Web3("HTTP://127.0.0.1:7545");

// 👇 Use Ganache account address here
const sender = "0xad888a672aE96363847d6196fBC938147c89B081";

app.post("/send", async (req, res) => {
  const { receiver, amount } = req.body;

  try {
    const receipt = await web3.eth.sendTransaction({
      from: sender,
      to: receiver,
      value: web3.utils.toWei(amount, "ether"),
      gas: 21000,
    });

    res.json({
      status: "success",
      transactionHash: receipt.transactionHash,
      blockNumber: receipt.blockNumber,
    });

  } catch (err) {
    res.json({
      status: "error",
      error: err.message,
    });
  }
});

app.listen(3000, () => {
  console.log("✅ Server running on http://localhost:3000");
});
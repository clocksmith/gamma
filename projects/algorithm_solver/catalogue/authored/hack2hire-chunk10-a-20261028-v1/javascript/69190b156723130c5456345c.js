"use strict";
// Hack2Hire 69190b156723130c5456345c (Design ChatBot System, variant 1 of 2) over an INFERRED spec; qualification unknown.

class EchoBot { react(text) { return text.startsWith("/echo ") ? text.slice(6) : null; } }
class ReverseBot { react(text) { return text.startsWith("/reverse ") ? [...text.slice(9)].reverse().join("") : null; } }
class CountBot { react(text, userMessages) { return text === "/count" ? String(userMessages) : null; } }
const BOT_TYPES = new Map([["echo", EchoBot], ["reverse", ReverseBot], ["count", CountBot]]); // new bot types only extend this table

class Channel {
  constructor() { this.log = []; this.bots = []; this.names = new Set(); this.userMessages = 0; }

  addBot(name, kind) {
    const Factory = BOT_TYPES.get(kind);
    if (Factory === undefined || this.names.has(name)) return false;
    this.names.add(name);
    this.bots.push([name, new Factory()]);
    return true;
  }

  send(user, text) {
    this.userMessages += 1;
    this.log.push(user + ": " + text);
    for (const [name, bot] of this.bots) {
      const reply = bot.react(text, this.userMessages);
      if (reply !== null) this.log.push(name + ": " + reply);
    }
  }

  recent(k) { return this.log.slice(Math.max(0, this.log.length - k)); }
}

class ChatApp {
  constructor() { this.channel = new Channel(); }
  addBot(botName, botType) { return this.channel.addBot(botName, botType); }
  sendMessage(userId, text) { this.channel.send(userId, text); }
  getRecentMessages(k) { return this.channel.recent(k); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ChatApp" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new ChatApp(...argumentLists[0]);
  const allowed = new Set(["addBot", "sendMessage", "getRecentMessages"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ChatApp = ChatApp;

"use strict";
// Hack2Hire 691b8695419c66014d71411a (Design ChatBot System, variant 2 of 2) over an INFERRED spec; qualification unknown.

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
  constructor() { this.channels = new Map(); }

  createChannel(channelId) {
    if (this.channels.has(channelId)) return false;
    this.channels.set(channelId, new Channel());
    return true;
  }

  addBot(channelId, botName, botType) {
    const channel = this.channels.get(channelId);
    return channel !== undefined && channel.addBot(botName, botType);
  }

  sendMessage(channelId, userId, text) {
    const channel = this.channels.get(channelId);
    if (channel === undefined) return false;
    channel.send(userId, text);
    return true;
  }

  getRecentMessages(channelId, k) {
    const channel = this.channels.get(channelId);
    return channel === undefined ? [] : channel.recent(k);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ChatApp" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new ChatApp(...argumentLists[0]);
  const allowed = new Set(["createChannel", "addBot", "sendMessage", "getRecentMessages"]);
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

import { GameSession } from './game-session.js';
import { generateChoices } from './game-logic.js';
import { EventBus } from '../utils/event-bus.js';

export class GameController {
  constructor(engine, config) {
    this.engine = engine;
    this.config = config;
    this.session = new GameSession(config);
    this.context = config.initialPrompt || 'The artificial intelligence revolution began when';
    this.isRunning = false;
    this.resolveChoice = null;
    this.resolveContinue = null;
  }

  async runRound() {
    const inputIds = this.engine.encode(this.context);

    const prediction = await this.engine.predictNext(inputIds, {
      temperature: this.config.temperature,
      topK: this.config.topK,
      topP: this.config.topP
    });

    const { choices, correctIndex, correctToken } = generateChoices(
      prediction.topTokens,
      this.engine,
      this.config.numChoices
    );

    EventBus.emit('round:start', {
      roundNum: this.session.currentRound + 1,
      maxRounds: this.config.maxRounds,
      context: this.context,
      choices,
      attention: prediction.attention,
      topTokens: prediction.topTokens,
      probStages: {
        raw: prediction.logitsRaw,
        temperature: prediction.stages.temperature,
        topK: prediction.stages.topK,
        topP: prediction.stages.topP,
        final: prediction.probabilities
      }
    });

    const playerChoice = await this.waitForPlayerChoice();

    const isCorrect = playerChoice === correctIndex;
    this.session.recordRound({
      context: this.context,
      choices,
      playerChoice,
      correctChoice: correctIndex,
      isCorrect,
      probabilities: prediction.probabilities
    });

    const isLastRound = this.session.currentRound >= this.config.maxRounds;

    EventBus.emit('round:result', {
      isCorrect,
      correctToken,
      correctChoice: correctIndex,
      playerChoice,
      probabilities: prediction.topTokens,
      isLastRound,
      finalScore: isLastRound ? this.session.score : null,
      maxRounds: this.config.maxRounds,
      score: this.session.score,
      streak: this.session.streak || 0
    });

    this.context += correctToken.text;
    return isCorrect;
  }

  async waitForPlayerChoice() {
    return new Promise(resolve => {
      this.resolveChoice = resolve;
    });
  }

  submitChoice(index) {
    if (this.resolveChoice) {
      this.resolveChoice(index);
      this.resolveChoice = null;
    }
  }

  async waitForContinue() {
    return new Promise(resolve => {
      this.resolveContinue = resolve;
    });
  }

  triggerContinue() {
    if (this.resolveContinue) {
      this.resolveContinue();
      this.resolveContinue = null;
    }
  }

  async runGame() {
    this.isRunning = true;
    EventBus.emit('game:start', { session: this.session });

    for (let i = 0; i < this.config.maxRounds && this.isRunning; i++) {
      await this.runRound();
      await this.waitForContinue();
    }

    EventBus.emit('game:end', {
      score: this.session.score,
      maxRounds: this.config.maxRounds,
      achievements: this.session.achievements
    });

    await this.session.save();
  }
}
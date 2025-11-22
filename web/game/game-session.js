import { Storage } from '../utils/storage.js';
import { EventBus } from '../utils/event-bus.js';

export class GameSession {
  constructor(config) {
    this.config = config;
    this.rounds = [];
    this.currentRound = 0;
    this.score = 0;
    this.streak = 0;
    this.maxStreak = 0;
    this.achievements = [];
    this.startTime = Date.now();
  }

  recordRound(result) {
    this.rounds.push({
      roundNum: this.currentRound,
      ...result,
      timestamp: Date.now()
    });

    if (result.isCorrect) {
      this.score++;
      this.streak++;
      this.maxStreak = Math.max(this.maxStreak, this.streak);
      this.checkAchievements();
    } else {
      this.streak = 0;
    }

    this.currentRound++;
  }

  checkAchievements() {
    if (this.streak === 3 && !this.achievements.includes('streak3')) {
      this.achievements.push('streak3');
      EventBus.emit('achievement', { 
        id: 'streak3', 
        name: 'Hot Streak', 
        desc: '3 correct in a row' 
      });
    }
  }

  async save() {
    await Storage.saveSession({
      timestamp: this.startTime,
      score: this.score,
      maxStreak: this.maxStreak,
      rounds: this.rounds
    });
  }
}
#!/usr/bin/env node
/**
 * Benchmark Query CLI
 *
 * Interactive command-line interface for querying benchmark results.
 * Answers natural language questions about model performance.
 */

import { BenchmarkQueryEngine } from './query_interface.js';
import readline from 'readline';

async function runInteractiveMode() {
  const queryEngine = new BenchmarkQueryEngine('./results');

  console.log('\n' + '='.repeat(80));
  console.log('🔍 GAMMA Benchmark Query Interface');
  console.log('='.repeat(80));
  console.log('\nAsk questions about model performance in natural language.');
  console.log('Examples:');
  console.log('  - "Which model should I use for Python coding?"');
  console.log('  - "What\'s the cheapest model with good quality?"');
  console.log('  - "Compare GPT-4 vs Claude for speed"');
  console.log('\nType "exit" or "quit" to exit.\n');

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const askQuestion = () => {
    rl.question('❓ Your question: ', async (question) => {
      if (['exit', 'quit', 'q'].includes(question.toLowerCase().trim())) {
        console.log('\nThank you for using GAMMA Benchmark Query! 👋\n');
        rl.close();
        return;
      }

      if (!question.trim()) {
        askQuestion();
        return;
      }

      try {
        const answer = await queryEngine.answerQuestion(question);
        displayAnswer(answer);
      } catch (error) {
        console.log(`\n❌ Error: ${error.message}\n`);
      }

      askQuestion();
    });
  };

  askQuestion();
}

function displayAnswer(answer) {
  console.log('\n' + '─'.repeat(80));

  if (answer.recommendation) {
    console.log(`\n✅ Recommendation: ${answer.recommendation}`);

    if (answer.confidence !== undefined) {
      const stars = '★'.repeat(Math.round(answer.confidence * 5));
      console.log(`   Confidence: ${(answer.confidence * 100).toFixed(0)}% ${stars}`);
    }

    if (answer.reasoning) {
      console.log(`   Reasoning: ${answer.reasoning}`);
    }

    if (answer.stats) {
      console.log('\n   📊 Statistics:');
      Object.entries(answer.stats).forEach(([key, value]) => {
        const formatted = typeof value === 'number'
          ? (value < 1 ? value.toFixed(3) : value.toFixed(1))
          : value;
        console.log(`      ${key}: ${formatted}`);
      });
    }

    if (answer.alternatives && answer.alternatives.length > 0) {
      console.log('\n   🔄 Alternatives:');
      answer.alternatives.forEach((alt, i) => {
        console.log(`      ${i + 1}. ${alt.model} - ${alt.reason}`);
      });
    }

    if (answer.savings) {
      console.log('\n   💰 Potential Savings:');
      Object.entries(answer.savings).forEach(([key, value]) => {
        console.log(`      ${key}: ${value}`);
      });
    }

    if (answer.speed_advantage) {
      console.log(`\n   ⚡ ${answer.speed_advantage}`);
    }

    if (answer.quality_advantage) {
      console.log(`\n   🎯 ${answer.quality_advantage}`);
    }

  } else if (answer.error) {
    console.log(`\n❌ ${answer.error}`);

    if (answer.suggestion) {
      console.log(`   💡 Suggestion: ${answer.suggestion}`);
    }

    if (answer.best_quality) {
      console.log(`\n   Highest quality option: ${answer.best_quality.recommendation}`);
    }

    if (answer.cheapest) {
      console.log(`   Cheapest viable option: ${answer.cheapest.model}`);
    }

  } else if (answer.models) {
    // Comparison result
    console.log('\n📊 Model Comparison\n');

    Object.entries(answer.dimensions).forEach(([dim, scores]) => {
      const winner = answer.winner_by_dimension[dim];
      console.log(`   ${dim.toUpperCase()}:`);
      Object.entries(scores).forEach(([model, score]) => {
        const isWinner = model === winner;
        const marker = isWinner ? ' 👑' : '   ';
        const bar = '█'.repeat(Math.round(score / 10));
        console.log(`     ${marker} ${model}: ${bar} ${score.toFixed(2)}`);
      });
      console.log();
    });

    console.log(`   🏆 Overall Winner: ${answer.overall_winner}\n`);
  }

  console.log('─'.repeat(80) + '\n');
}

async function runSingleQuery(query) {
  const queryEngine = new BenchmarkQueryEngine('./results');

  console.log('\n🔍 Query:', query);

  try {
    const answer = await queryEngine.answerQuestion(query);
    displayAnswer(answer);
  } catch (error) {
    console.log(`\n❌ Error: ${error.message}\n`);
    process.exit(1);
  }
}

// Main
const args = process.argv.slice(2);

if (args.length === 0) {
  runInteractiveMode();
} else if (args[0] === '--help' || args[0] === '-h') {
  console.log(`
GAMMA Benchmark Query CLI

Usage:
  node query_cli.js                 # Interactive mode
  node query_cli.js "your question" # Single query

Examples:
  node query_cli.js "Which model should I use for Python coding?"
  node query_cli.js "What's the fastest model above 80% quality?"
  node query_cli.js "Compare GPT-4 and Claude"

  `);
} else {
  runSingleQuery(args.join(' '));
}

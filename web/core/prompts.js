export const STARTING_PROMPTS = [
  // Science & Technology
  "The artificial intelligence revolution began when",
  "Scientists discovered that quantum computers could",
  "The first human colony on Mars was",
  "When the internet was invented, nobody expected",
  "The breakthrough in fusion energy came after",
  "Genetic engineering has allowed us to",
  "The robot looked at its hands and",
  "Climate change accelerated when researchers found",

  // Stories & Fiction
  "Once upon a time in a distant kingdom",
  "The detective examined the crime scene and",
  "She opened the ancient book and read",
  "The spaceship landed silently in the",
  "He knew something was wrong when the",
  "The dragon emerged from the cave with",
  "In the year 3000, humanity had",
  "The witch's spell went terribly wrong because",

  // Philosophy & Thought
  "The meaning of life has always been",
  "Philosophers have long debated whether free will",
  "The nature of consciousness remains one of",
  "If a tree falls in the forest",
  "The greatest challenge facing humanity today is",
  "What separates humans from machines is our",

  // History & Culture
  "The ancient Egyptians built the pyramids using",
  "During the Renaissance, artists began to",
  "The industrial revolution transformed society by",
  "When explorers first reached the New World",
  "The fall of Rome was caused by",
  "Medieval knights were trained from childhood to",

  // Nature & Animals
  "Deep in the ocean, creatures have evolved",
  "The migration patterns of birds tell us",
  "Wolves communicate with each other through",
  "The rainforest contains species that scientists",
  "When winter comes, bears prepare by",
  "The oldest trees on Earth have witnessed",

  // Everyday Life
  "The best way to start your morning is",
  "When cooking a perfect meal, you should",
  "The secret to a happy relationship is",
  "Learning a new language requires patience and",
  "The most important skill in the workplace is",
  "Good friends are hard to find because",

  // Economics & Business
  "The stock market crashed when investors realized",
  "Successful entrepreneurs often share the trait of",
  "The global economy depends heavily on",
  "Cryptocurrency has changed how we think about",

  // Psychology & Mind
  "Dreams may be the brain's way of",
  "Memory works by storing information in",
  "People make decisions based on emotions rather",
  "The fear of public speaking comes from",

  // Art & Creativity
  "The greatest paintings in history capture",
  "Music has the power to make us",
  "Writers find inspiration by observing the",
  "Architecture reflects the values of the"
];

export function getRandomPrompt() {
  return STARTING_PROMPTS[Math.floor(Math.random() * STARTING_PROMPTS.length)];
}

export async function fetchUserData(userId) {
  if (typeof userId !== 'number' || userId < 1) {
    throw new Error('Invalid userId');
  }

  await new Promise(resolve => setTimeout(resolve, 300));

  return {
    id: userId,
    name: `User ${userId}`,
    email: `user${userId}@example.com`,
  };
}

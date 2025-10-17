export async function fetchUserData(userId) {
  if (typeof userId !== 'number' || userId < 1) {
    throw new Error('Invalid userId');
  }

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        id: userId,
        name: `User ${userId}`,
        email: `user${userId}@example.com`,
      });
    }, 300);
  });
}

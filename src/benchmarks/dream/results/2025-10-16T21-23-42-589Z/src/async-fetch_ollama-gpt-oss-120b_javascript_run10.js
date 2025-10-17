export async function fetchUserData(userId) {
  return new Promise((resolve, reject) => {
    if (typeof userId !== 'number' || userId < 1) {
      reject(new Error('Invalid userId'));
      return;
    }

    setTimeout(() => {
      resolve({
        id: userId,
        name: `User ${userId}`,
        email: `user${userId}@example.com`,
      });
    }, 300);
  });
}

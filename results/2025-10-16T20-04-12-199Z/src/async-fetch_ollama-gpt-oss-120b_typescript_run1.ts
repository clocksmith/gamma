export interface UserData {
  id: number;
  name: string;
  email: string;
}

export async function fetchUserData(userId: number): Promise<UserData> {
  if (userId < 1) {
    return Promise.reject(new Error('Invalid userId'));
  }

  return new Promise<UserData>((resolve) => {
    setTimeout(() => {
      resolve({
        id: userId,
        name: `User ${userId}`,
        email: `user${userId}@example.com`,
      });
    }, 300);
  });
}

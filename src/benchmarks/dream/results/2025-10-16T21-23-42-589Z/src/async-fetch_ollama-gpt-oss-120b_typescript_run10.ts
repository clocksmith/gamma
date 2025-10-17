export interface UserData {
  id: number;
  name: string;
  email: string;
}

export async function fetchUserData(userId: number): Promise<UserData> {
  return new Promise<UserData>((resolve, reject) => {
    if (userId < 1) {
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

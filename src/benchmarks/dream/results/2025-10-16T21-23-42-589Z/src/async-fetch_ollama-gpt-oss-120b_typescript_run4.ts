export interface UserData {
  id: number;
  name: string;
  email: string;
}

/**
 * Simulates fetching user data from an API.
 * @param userId - The ID of the user to fetch (must be >= 1).
 * @returns A promise that resolves with the user data.
 * @throws An error if `userId` is less than 1.
 */
export async function fetchUserData(userId: number): Promise<UserData> {
  if (userId < 1) {
    throw new Error('Invalid userId: must be greater than 0');
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
